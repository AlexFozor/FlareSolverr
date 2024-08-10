# -*- coding:utf-8 -*-
"""
@Author  :   g1879
@Contact :   g1879@qq.com
@File    :   downloadKit.py
"""
from copy import copy
from pathlib import Path
from queue import Queue
from re import sub
from threading import Thread, Lock
from time import sleep, perf_counter

from requests import Response
from requests.structures import CaseInsensitiveDict

from ._funcs import FileExistsSetter, PathSetter, BlockSizeSetter, set_charset, get_file_info, get_file_exists_mode
from .mission import Task, Mission
from .setter import Setter


class DownloadKit(object):
    file_exists = FileExistsSetter()
    goal_path = PathSetter()
    block_size = BlockSizeSetter()

    def __init__(self, goal_path=None, roads=10, session=None, file_exists='rename', driver=None):
        """
        :param goal_path: 文件保存路径
        :param roads: 可同时运行的线程数
        :param file_exists: 有同名文件名时的处理方式，可选 'skip', 'overwrite', 'rename', 'add'
        :param driver: 使用的Session对象，或配置对象、页面对象等
        """
        self._roads = roads
        self._missions = {}
        self._threads = {i: None for i in range(self._roads)}
        self._waiting_list = Queue()
        self._missions_num = 0
        self._running_count = 0  # 正在运行的任务数
        self._stop_printing = False  # 用于控制显示线程停止
        self._lock = Lock()
        self.page = None
        self._retry = None
        self._interval = None
        self._timeout = None
        self._encoding = None

        self._setter = None
        self._print_mode = None
        self._log_mode = None
        self._logger = None

        self.goal_path = goal_path or '.'
        self.file_exists = file_exists
        self.split = True
        self.block_size = '50M'
        self.set.driver(session or driver)

    def __call__(self, file_url, goal_path=None, rename=None, suffix=None, file_exists=None, show_msg=True, **kwargs):
        """以阻塞的方式下载一个文件并返回结果
        :param file_url: 文件网址
        :param goal_path: 保存路径
        :param rename: 重命名的文件名
        :param suffix: 指定后缀名
        :param file_exists: 遇到同名文件时的处理方式，可选 'skip', 'overwrite', 'rename', 'add'，默认跟随实例属性
        :param show_msg: 是否打印进度
        :param kwargs: 连接参数
        :return: 任务结果和信息组成的tuple
        """
        return self.download(file_url=file_url, goal_path=goal_path, rename=rename, suffix=suffix,
                             file_exists=file_exists, show_msg=show_msg, **kwargs)

    @property
    def set(self):
        """用于设置打印和记录模式的对象"""
        if self._setter is None:
            self._setter = Setter(self)
        return self._setter

    @property
    def roads(self):
        """可同时运行的线程数"""
        return self._roads

    @property
    def retry(self):
        """返回连接失败时重试次数"""
        if self._retry is not None:
            return self._retry
        elif self.page is not None:
            return self.page.retry_times
        else:
            return 3

    @property
    def interval(self):
        """返回连接失败时重试间隔"""
        if self._interval is not None:
            return self._interval
        elif self.page is not None:
            return self.page.retry_interval
        else:
            return 5

    @property
    def timeout(self):
        """返回连接超时时间"""
        if self._timeout is not None:
            return self._timeout
        elif self.page is not None:
            return self.page.timeout
        else:
            return 20

    @property
    def waiting_list(self):
        """返回等待队列"""
        return self._waiting_list

    @property
    def session(self):
        """返回用于保存默认连接设置的Session对象"""
        return self._session

    @property
    def is_running(self):
        """返回是否有线程还在运行"""
        return self._running_count > 0

    @property
    def missions(self):
        """用list方式返回所有任务对象"""
        return self._missions

    @property
    def encoding(self):
        """返回指定的编码格式"""
        return self._encoding

    def add(self, file_url, goal_path=None, rename=None, suffix=None, file_exists=None, split=None, **kwargs):
        """添加一个下载任务并将其返回
        :param file_url: 文件网址
        :param goal_path: 保存路径
        :param rename: 重命名的文件名
        :param suffix: 重命名的文件后缀名
        :param file_exists: 遇到同名文件时的处理方式，可选 'skip', 'overwrite', 'rename', 'add'，默认跟随实例属性
        :param split: 是否允许多线程分块下载，为None则使用对象属性
        :param kwargs: 连接参数
        :return: 任务对象
        """
        self._missions_num += 1
        self._running_count += 1
        if file_exists is not None:
            file_exists = get_file_exists_mode(file_exists)
        mission = Mission(self._missions_num, self, file_url, str(goal_path or self.goal_path), rename, suffix,
                          file_exists or self.file_exists, self.split if split is None else split, self._encoding,
                          kwargs)
        self._missions[self._missions_num] = mission
        self._run_or_wait(mission)
        return mission

    def download(self, file_url, goal_path=None, rename=None, suffix=None, file_exists=None, show_msg=True, **kwargs):
        """以阻塞的方式下载一个文件并返回结果
        :param file_url: 文件网址
        :param goal_path: 保存路径
        :param rename: 重命名的文件名
        :param suffix: 重命名的文件后缀名
        :param file_exists: 遇到同名文件时的处理方式，可选 'skip', 'overwrite', 'rename', 'add'，默认跟随实例属性
        :param show_msg: 是否打印进度
        :param kwargs: 连接参数
        :return: 任务结果和信息组成的tuple
        """
        if show_msg:
            tmp = self._print_mode
            self._print_mode = None
        r = self.add(file_url=file_url, goal_path=goal_path, rename=rename, suffix=suffix, file_exists=file_exists,
                     split=False, **kwargs).wait(show=show_msg)
        if show_msg:
            self._print_mode = tmp
        return r

    def _run_or_wait(self, mission):
        """接收任务，有空线程则运行，没有则进入等待队列
        :param mission: 任务对象
        :return: None
        """
        thread_id = self._get_usable_thread()
        if thread_id is not None:
            thread = Thread(target=self._run, args=(thread_id, mission), daemon=False)
            self._threads[thread_id] = {'thread': thread, 'mission': None}
            thread.start()
        else:
            self._waiting_list.put(mission)

    def _run(self, ID, mission):
        """线程函数
        :param ID: 线程id
        :param mission: 任务对象，Mission或Task
        :return: None
        """
        while True:
            if not mission:  # 如果没有任务，就从等候列表中取一个
                if not self._waiting_list.empty():
                    try:
                        mission = self._waiting_list.get(True, .5)
                    except Exception:
                        self._waiting_list.task_done()
                        break
                else:
                    break

            self._threads[ID]['mission'] = mission
            self._download(mission, ID)
            mission = None

        self._threads[ID] = None

    def get_mission(self, mission_or_id):
        """根据id值获取一个任务
        :param mission_or_id: 任务或任务id
        :return: 任务对象
        """
        return self._missions[mission_or_id] if isinstance(mission_or_id, int) else mission_or_id

    def get_failed_missions(self):
        """返回失败任务列表"""
        return [i for i in self._missions.values() if i.result is False]

    def wait(self, mission=None, show=False, timeout=None):
        """等待所有或指定任务完成
        :param mission: 任务对象或任务id，为None时等待所有任务结束
        :param show: 是否显示进度
        :param timeout: 超时时间，None或0为无限
        :return: 任务结果和信息组成的tuple
        """
        timeout = 0 if timeout is None else timeout
        if mission:
            return self.get_mission(mission).wait(show, timeout)

        else:
            if show:
                self.show(False)
            else:
                end_time = perf_counter() + timeout
                while self.is_running and (perf_counter() < end_time or timeout == 0):
                    sleep(0.1)

    def cancel(self):
        """取消所有等待中或执行中的任务"""
        for m in self._missions.values():
            m.cancel()

    def show(self, asyn=True, keep=False):
        """实时显示所有线程进度
        :param asyn: 是否以异步方式显示
        :param keep: 任务列表为空时是否保持显示
        :return: None
        """
        if asyn:
            Thread(target=self._show, args=(2, keep)).start()
        else:
            self._show(0.1, keep)

    def _show(self, wait, keep=False):
        """实时显示所有线程进度
        :param wait: 超时时间（秒）
        :param keep: 任务列表为空时是否保持显示
        :return: None
        """
        self._stop_printing = False

        if keep:
            Thread(target=self._stop_show).start()

        end_time = perf_counter() + wait
        while not self._stop_printing and (keep or self.is_running or perf_counter() < end_time):
            print(f'\033[K', end='')
            print(f'等待任务数：{self._waiting_list.qsize()}')
            for k, v in self._threads.items():
                m = v['mission'] if v else None
                if m:
                    items = (m.mission.rate, m.mid) if isinstance(m, Task) else (m.rate, m.id)
                    path = f'M{items[1]} {items[0]}% {m}'
                else:
                    path = '空闲'
                print(f'\033[K', end='')
                print(f'线程{k}：{path}')

            print(f'\033[{self.roads + 1}A\r', end='')
            sleep(0.4)

        print(f'\033[1B', end='')
        for i in range(self.roads):
            print(f'\033[K', end='')
            print(f'线程{i}：空闲')

        print()

    def _connect(self, url, session, _headers, method, encoding, **kwargs):
        """生成response对象
        :param url: 目标url
        :param session: 用于连接的Session对象
        :param _headers: 内置的headers参数
        :param method: 请求方式
        :param encoding: 编码格式
        :param kwargs: 连接参数
        :return: tuple，第一位为Response或None，第二位为出错信息或'Success'
        """
        if 'headers' in kwargs:  # 不知道为什么添加这个才能正常使用多线程
            kwargs['headers'] = CaseInsensitiveDict({**_headers, **kwargs['headers']})
        else:
            kwargs['headers'] = _headers

        r = err = None
        for i in range(self.retry + 1):
            try:
                if method == 'get':
                    r = session.get(url, **kwargs)
                elif method == 'post':
                    r = session.post(url, **kwargs)

                if r:
                    return set_charset(r, encoding), 'Success'

            except Exception as e:
                err = e

            if r and r.status_code in (403, 404):
                break
            if i < self.retry:
                sleep(self.interval)

        # 返回失败结果
        if r is None:
            return None, '连接失败' if err is None else err
        if not r.ok:
            return r, f'状态码：{r.status_code}'

    def _get_usable_thread(self):
        """获取可用线程，没有则返回None"""
        for k, v in self._threads.items():
            if v is None:
                return k

    def _stop_show(self):
        """设置停止打印的变量"""
        input()
        self._stop_printing = True

    def _when_mission_done(self, mission):
        """当任务完成时执行的操作
        :param mission: 完结的任务
        :return: None
        """
        self._running_count -= 1
        if self._print_mode == 'all' or (self._print_mode == 'failed' and mission.result is False):
            print(f'[{mission.RESULT_TEXTS[mission.result]}] {mission.data.url} {mission.info}')

        if self._log_mode == 'all' or (self._log_mode == 'failed' and mission.result is False):
            data = ('下载结果',
                    mission.data.url,
                    mission.data.goal_path,
                    mission.data.rename,
                    mission.data.kwargs)
            self._logger.add_data(data)

        mission.session.close()

    def _download(self, mission_or_task, thread_id):
        """此方法是执行下载的线程方法，用于根据任务下载文件
        :param mission_or_task: 下载任务对象
        :param thread_id: 线程号
        :return: None
        """
        if mission_or_task.is_done:
            return
        if mission_or_task.state == 'cancel':
            mission_or_task.state = 'done'
            return

        file_url = mission_or_task.data.url

        if isinstance(mission_or_task, Task):
            kwargs = copy(mission_or_task.data.kwargs)
            task = mission_or_task
            kwargs['headers']['Range'] = f"bytes={task.range[0]}-{task.range[1]}"
            r, inf = self._connect(file_url, task.mission.session, task.mission.headers, task.mission.method,
                                   task.mission.encoding, **kwargs)

            if r:
                _do_download(r, task, False)
            else:
                task._set_done(False, inf)

            return

        # ===================开始处理mission====================
        mission = mission_or_task
        mission.info = '下载中'
        mission.state = 'running'
        kwargs = mission_or_task.data.kwargs
        if self._print_mode == 'all':
            print(f'开始下载：{mission.data.url}')
        if self._log_mode == 'all':
            self._logger.add_data(('开始下载', mission.data.url))

        rename = mission.data.rename
        suffix = mission.data.suffix
        goal_path = mission.data.goal_path
        file_exists = mission.data.file_exists
        split = mission.data.split

        goal_Path = Path(goal_path)
        # 按windows规则去除路径中的非法字符
        g = goal_path[len(goal_Path.anchor):] if goal_path.lower().startswith(goal_Path.anchor.lower()) else goal_path
        goal_path = goal_Path.anchor + sub(r'[*:|<>?"]', '', g).strip()
        goal_Path = Path(goal_path).absolute()
        goal_Path.mkdir(parents=True, exist_ok=True)
        goal_path = str(goal_Path)

        if file_exists == 'skip' and rename:
            tmp = goal_Path / rename
            if tmp.exists() and tmp.is_file():
                mission.file_name = rename
                mission._set_path(goal_Path / rename)
                mission._set_done('skipped', str(mission.path))
                return

        r, inf = self._connect(file_url, mission.session, mission.headers, mission.method, mission.encoding, **kwargs)

        if mission.is_done:
            return

        if not r:
            mission._break_mission(result=False, info=inf)
            return

        # -------------------获取文件信息-------------------
        file_info = get_file_info(r, goal_path, rename, suffix, file_exists, mission.encoding, self._lock)
        file_size = file_info['size']
        full_path = file_info['path']
        mission._set_path(full_path)
        mission.file_name = full_path.name
        mission.size = file_size

        if file_info['skip']:
            mission._set_done('skipped', str(mission.path))
            return

        full_Path = Path(full_path)
        if file_exists == 'add' and full_Path.exists():
            mission.data.offset = full_Path.stat().st_size

        # -------------------设置分块任务-------------------
        first = False
        if split and file_size and file_size > self.block_size and r.headers.get('Accept-Ranges') == 'bytes':
            first = True
            chunks = [[s, min(s + self.block_size, file_size) - 1] for s in range(0, file_size, self.block_size)]
            chunks[-1][-1] = ''
            chunks_len = len(chunks)

            task1 = Task(mission, chunks[0], f'1/{chunks_len}', chunks[0][1] - chunks[0][0])
            mission.tasks_count = chunks_len
            mission.tasks = [task1]

            for ind, chunk in enumerate(chunks[1:], 2):
                s = file_size - chunk[0] if chunks_len == ind else chunk[1] - chunk[0]
                task = Task(mission, chunk, f'{ind}/{chunks_len}', s)
                mission.tasks.append(task)
                self._run_or_wait(task)

        else:  # 不分块
            task1 = Task(mission, None, '1/1', file_size)
            mission.tasks.append(task1)

        self._threads[thread_id]['mission'] = task1
        _do_download(r, task1, first)


def _do_download(r: Response, task: Task, first: bool = False):
    """执行下载任务
    :param r: Response对象
    :param task: 任务
    :param first: 是否第一个分块
    :return: None
    """
    if task.is_done or task.mission.is_done:
        return

    task.set_states(result=None, info='下载中', state='running')
    block_size = 131072  # 128k
    result = None

    try:
        if first:  # 分块是第一块
            if task.range[1] <= block_size or task.range[1] % block_size != 0:
                r_content = r.iter_content(chunk_size=task.range[1] + 1)
                task.add_data(next(r_content), seek=0 + task.mission.data.offset)
                if task.state in ('cancel', 'done'):
                    result = 'canceled'
                    task.clear_cache()

            else:
                blocks = task.range[1] // block_size
                remainder = task.range[1] % block_size
                r_content = r.iter_content(chunk_size=block_size)
                for b in range(blocks):
                    task.add_data(next(r_content), seek=b * block_size + task.mission.data.offset)
                    if task.state in ('cancel', 'done'):
                        result = 'canceled'
                        task.clear_cache()
                        break

                if task.state in ('cancel', 'done'):
                    result = 'canceled'
                    task.clear_cache()
                else:
                    task.add_data(next(r_content)[:remainder + 1], blocks * block_size + task.mission.data.offset)

        else:
            if task.range is None:  # 不分块
                for chunk in r.iter_content(chunk_size=block_size):
                    if task.state in ('cancel', 'done'):
                        result = 'canceled'
                        task.clear_cache()
                        break
                    if chunk:
                        task.add_data(chunk, None)

            elif task.range[1] == '':  # 结尾的数据块
                begin = task.range[0]
                for chunk in r.iter_content(chunk_size=block_size):
                    if task.state in ('cancel', 'done'):
                        result = 'canceled'
                        task.clear_cache()
                        break
                    if chunk:
                        task.add_data(chunk, seek=begin + task.mission.data.offset)
                        begin += len(chunk)

            else:  # 有始末数字的数据块
                begin, end = task.range
                num = (end - begin) // block_size
                for ind, chunk in enumerate(r.iter_content(chunk_size=block_size), 1):
                    if task.state in ('cancel', 'done'):
                        result = 'canceled'
                        task.clear_cache()
                        break
                    if chunk:
                        task.add_data(chunk, seek=begin + task.mission.data.offset)
                        if ind <= num:
                            begin += block_size

    except Exception as e:
        result, info = False, f'下载失败。{r.status_code} {e}'

    else:
        result = 'success' if result is None else result
        info = str(task.path)

    finally:
        r.close()

    task._set_done(result=result, info=info)
