# -*- coding:utf-8 -*-
"""
@Author  :   g1879
@Contact :   g1879@qq.com
"""
from pathlib import Path
from time import sleep, perf_counter
from urllib.parse import quote, urlparse

from ..DataRecorder import ByteRecorder
from requests.structures import CaseInsensitiveDict

from ._funcs import copy_session, set_session_cookies


class MissionData(object):
    def __init__(self, url, goal_path, rename, suffix, file_exists, split, kwargs, offset=0):
        """保存任务数据的对象
        :param url: 下载文件url
        :param goal_path: 保存文件夹
        :param rename: 文件重命名
        :param suffix: 文件重命名后缀名
        :param file_exists: 存在重名文件时处理方式
        :param split: 是否允许分块下载
        :param kwargs: requests其它参数
        :param offset: 文件存储偏移量
        """
        self.url = quote(url, safe='-_.~!*\'"();:@&=+$,/\\?#[]%')
        self.goal_path = goal_path
        self.rename = rename
        self.suffix = suffix
        self.file_exists = file_exists
        self.split = split
        self.kwargs = kwargs
        self.offset = offset


class BaseTask(object):
    _DONE = 'done'
    RESULT_TEXTS = {'success': '成功', 'skipped': '跳过', 'canceled': '取消', False: '失败', None: '未知'}

    def __init__(self, ID):
        """任务类基类
        :param ID: 任务id
        """
        self._id = ID
        self.state = 'waiting'  # 'waiting'、'running'、'done'
        self.result = None  # 'success'、'skipped'、'canceled'、False、None
        self.info = '等待下载'  # 信息

    @property
    def id(self):
        """返回任务或子任务id"""
        return self._id

    @property
    def data(self):
        """返回任务数据"""
        return

    @property
    def is_done(self):
        """返回任务是否结束"""
        return self.state in ('done', 'cancel')

    def set_states(self, result=None, info=None, state='done'):
        """设置任务结果值
        :param result: 结果：'success'、'skipped'、'canceled'、False、None
        :param info: 任务信息
        :param state: 任务状态：'waiting'、'running'、'done'
        :return: None
        """
        self.result = result
        self.info = info
        self.state = state


class Mission(BaseTask):
    def __init__(self, ID, download_kit, file_url, goal_path, rename, suffix, file_exists, split, encoding, kwargs):
        """任务类
        :param ID: 任务id
        :param download_kit: 所属DownloadKit对象
        :param file_url: 文件网址
        :param goal_path: 保存文件夹路径
        :param rename: 重命名
        :param suffix: 重命名后缀名
        :param file_exists: 存在同名文件处理方式
        :param split: 是否分块下载
        :param encoding: 编码格式
        :param kwargs: 连接参数
        """
        super().__init__(ID)
        self.download_kit = download_kit
        self.size = None

        self.tasks = []
        self.tasks_count = 1
        self.done_tasks_count = 0

        self.file_name = None
        self._path = None  # 文件完整路径，Path对象
        self._recorder = None
        self.encoding = encoding

        self._set_session()
        kwargs = self._handle_kwargs(file_url, kwargs)
        self._data = MissionData(file_url, goal_path, rename, suffix, file_exists, split, kwargs)
        self.method = 'post' if (self._data.kwargs.get('data', None) is not None or
                                 self._data.kwargs.get('json', None) is not None) else 'get'

    def __repr__(self):
        return f'<Mission {self.id} {self.info} {self.file_name}>'

    @property
    def data(self):
        """返回任务数据"""
        return self._data

    @property
    def path(self):
        """返回文件保存路径"""
        return self._path

    @property
    def recorder(self):
        """返回记录器对象"""
        if self._recorder is None:
            self._recorder = ByteRecorder(cache_size=100)
            self._recorder.show_msg = False
        return self._recorder

    @property
    def rate(self):
        """返回下载进度百分比"""
        if not self.size:
            return None
        c = 0
        for t in self.tasks:
            c += t._downloaded_size if t._downloaded_size else 0
        return round((c / self.size) * 100, 2)

    def cancel(self) -> None:
        """取消该任务，停止未下载完的task"""
        self._break_mission('canceled', '已取消')

    def del_file(self):
        """删除下载的文件"""
        if self.path and self.path.exists():
            try:
                self.path.unlink()
            except Exception:
                pass

    def wait(self, show=True, timeout=0):
        """等待当前任务完成
        :param show: 是否显示下载进度
        :param timeout: 超时时间
        :return: 任务结果和信息组成的tuple
        """
        if show:
            print(f'url：{self.data.url}')
            t2 = perf_counter()
            while self.file_name is None and perf_counter() - t2 < 4:
                sleep(0.01)
            print(f'文件名：{self.file_name}')
            print(f'目标路径：{self.path}')
            if not self.size:
                print('未知大小 ', end='')

        t1 = perf_counter()
        while not self.is_done and (perf_counter() - t1 < timeout or timeout == 0):
            if show and self.size:
                try:
                    rate = round((self.path.stat().st_size / self.size) * 100, 2)
                    print(f'\r{rate}% ', end='')
                except FileNotFoundError:
                    pass

            sleep(0.1)

        if show:
            if self.result is False:
                print(f'下载失败 {self.info}')
            elif self.result == 'success':
                print('\r100% ', end='')
                print(f'下载完成 {self.info}')
            elif self.result == 'skipped':
                print(f'已跳过 {self.info}')
            print()

        return self.result, self.info

    def _set_session(self):
        """复制Session对象，并设置cookies"""
        session = copy_session(self.download_kit.session)
        headers = session.headers
        session.headers = None
        if self.download_kit.page:
            set_session_cookies(session, self.download_kit.page.cookies())
            if hasattr(self.download_kit.page, '_headers'):
                headers = CaseInsensitiveDict({**self.download_kit.page._headers, **headers})
            headers.update({"User-Agent": self.download_kit.page.user_agent})
        self.session = session
        self.headers = headers

    def _handle_kwargs(self, url, kwargs):
        """处理接收到的参数
        :param url: 要访问的url
        :param kwargs: 传入的参数dict
        :return: 处理后的参数dict
        """
        if 'timeout' not in kwargs:
            kwargs['timeout'] = self.download_kit.timeout

        headers = CaseInsensitiveDict(kwargs['headers']) if 'headers' in kwargs else CaseInsensitiveDict()

        parsed_url = urlparse(url)
        hostname = parsed_url.hostname
        scheme = parsed_url.scheme

        if not ('Referer' in headers or 'Referer' in self.headers):
            headers['Referer'] = self.download_kit.page.url if self.download_kit.page and self.download_kit.page.url \
                else f'{scheme}://{hostname}'
        if not ('Host' in headers or 'Host' in self.headers):
            headers['Host'] = hostname
        kwargs['headers'] = headers

        return kwargs

    def _set_path(self, path):
        """设置文件保存路径"""
        if isinstance(path, (Path, str)):
            path = Path(path)
            self.file_name = path.name

        self._path = path
        self.recorder.set.path(path)

    def _set_done(self, result, info):
        """设置一个任务为done状态
        :param result: 结果：'success'、'skipped'、'canceled'、False、None
        :param info: 任务信息
        :return: None
        """
        if result == 'skipped':
            self.set_states(result=result, info=info, state=self._DONE)

        elif result == 'canceled' or result is False:
            self.recorder.clear()
            self.set_states(result=result, info=info, state=self._DONE)

        elif result == 'success':
            self.recorder.record()
            if self.size and self.path.stat().st_size < self.size:
                self.del_file()
                self.set_states(False, '下载失败', self._DONE)
            else:
                self.set_states('success', info, self._DONE)

        self.download_kit._when_mission_done(self)

    def _a_task_done(self, is_success, info):
        """当一个task完成时调用
        :param is_success: 该task是否成功
        :param info: 该task传入的信息
        :return: None
        """
        if self.is_done:
            return

        if is_success is False:
            self._break_mission(False, info)
            return

        self.done_tasks_count += 1
        if self.done_tasks_count == self.tasks_count:
            self._set_done('success', info)

    def _break_mission(self, result, info):
        """中止该任务，停止未下载完的task
        :param result: 结果：'success'、'skipped'、'canceled'、False、None
        :param info: 任务信息
        :return: None
        """
        if self.is_done:
            return

        for task in self.tasks:
            if not task.is_done:
                task.set_states(result=result, info=info, state='cancel')

        while any((not i.is_done for i in self.tasks)):
            sleep(.3)

        self._set_done(result, info)
        self.del_file()


class Task(BaseTask):
    def __init__(self, mission, range_, ID, size):
        """子任务类
        :param mission: 父任务对象
        :param range_: 读取文件数据范围
        :param ID: 任务id
        """
        super().__init__(ID)
        self.mission = mission
        self.range = range_
        self.size = size
        self._downloaded_size = 0

    def __repr__(self):
        return f'<Task M{self.mid} T{self._id} {self.rate}% {self.info} {self.file_name}>'

    @property
    def mid(self):
        """返回父任务id"""
        return self.mission.id

    @property
    def data(self):
        """返回任务数据对象"""
        return self.mission.data

    @property
    def path(self):
        """返回文件保存路径"""
        return self.mission.path

    @property
    def file_name(self):
        """返回文件名"""
        return self.mission.file_name

    @property
    def rate(self):
        """返回下载进度百分比"""
        return round((self._downloaded_size / self.size) * 100, 2) if self.size else None

    def add_data(self, data, seek=None):
        """把数据输入到记录器
        :param data: 文件字节数据
        :param seek: 在文件中的位置，None表示最后
        :return: None
        """
        self._downloaded_size += len(data)
        self.mission.recorder.add_data(data, seek)

    def clear_cache(self):
        """清除以接收但未写入硬盘的缓存"""
        self.mission.recorder.clear()

    def _set_done(self, result, info):
        """设置一个子任务为done状态
        :param result: 结果：'success'、'skipped'、'canceled'、False、None
        :param info: 任务信息
        :return: None
        """
        self.set_states(result=result, info=info, state=self._DONE)
        self.mission._a_task_done(result, info)
