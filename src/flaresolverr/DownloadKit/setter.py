# -*- coding:utf-8 -*-
"""
@Author  :   g1879
@Contact :   g1879@qq.com
@File    :   setter.py
"""
from ..DataRecorder import Recorder
from requests import Session

from ._funcs import get_file_exists_mode


class Setter(object):
    def __init__(self, downloadKit):
        """
        :param downloadKit: downloadKit对象
        """
        self._downloadKit = downloadKit

    @property
    def if_file_exists(self):
        """返回用于设置文件同名策略的对象"""
        return FileExists(self)

    @property
    def log(self):
        """返回用于设置记录模式的对象"""
        return LogSet(self)

    def driver(self, driver):
        """设置Session对象
        :param driver: Session对象或DrissionPage的页面对象
        :return: None
        """
        if driver is None:
            self._downloadKit._session = Session()
            return

        elif isinstance(driver, Session):
            self._downloadKit._session = driver
            return

        _type = str(type(driver))
        if _type.startswith('<SessionOptions '):
            self._downloadKit._session, headers = driver.make_session()
            self._downloadKit._session.headers = headers
            return

        else:
            self._downloadKit._session = driver.session if hasattr(driver, 'session') else Session()
            self._downloadKit.page = driver

    def roads(self, num):
        """设置可同时运行的线程数
        :param num: 线程数量
        :return: None
        """
        if self._downloadKit.is_running:
            print('有任务未完成时不能改变roads。')
            return
        if num != self._downloadKit.roads:
            self._downloadKit._roads = num
            self._downloadKit._threads = {i: None for i in range(num)}

    def retry(self, times):
        """设置连接失败时重试次数
        :param times: 重试次数
        :return: None
        """
        if not isinstance(times, int) or times < 0:
            raise TypeError('times参数只能接受int格式且不能小于0。')
        self._downloadKit._retry = times

    def interval(self, seconds):
        """设置连接失败时重试间隔
        :param seconds: 连接失败时重试间隔（秒）
        :return: None
        """
        if not isinstance(seconds, (int, float)) or seconds < 0:
            raise TypeError('seconds参数只能接受int或float格式且不能小于0。')
        self._downloadKit._interval = seconds

    def timeout(self, seconds):
        """设置连接超时时间
        :param seconds: 超时时间（秒）
        :return: None
        """
        if not isinstance(seconds, (int, float)) or seconds < 0:
            raise TypeError('seconds参数只能接受int或float格式且不能小于0。')
        self._downloadKit._timeout = seconds

    def goal_path(self, path):
        """设置文件保存路径
        :param path: 文件路径，可以是str或Path
        :return: None
        """
        self._downloadKit.goal_path = path

    def split(self, on_off):
        """设置大文件是否分块下载
        :param on_off: bool代表开关
        :return: None
        """
        self._downloadKit.split = on_off

    def block_size(self, size):
        """设置分块大小
        :param size: 单位为字节，可用'K'、'M'、'G'为单位，如'50M'
        :return: None
        """
        self._downloadKit.block_size = size

    def proxies(self, http=None, https=None):
        """设置代理地址及端口，例：'127.0.0.1:1080'
        :param http: http代理地址及端口
        :param https: https代理地址及端口
        :return: None
        """
        self._downloadKit._session.proxies = {'http': http, 'https': https}

    def encoding(self, encoding):
        """设置编码
        :param encoding: 编码名称，传入None取消之前的设置
        :return: None
        """
        self._downloadKit._encoding = encoding if encoding else None


class LogSet(object):
    """用于设置信息打印和记录日志方式"""

    def __init__(self, setter):
        """
        :param setter: Setter对象
        """
        self._setter = setter

    def path(self, path):
        """设置日志文件路径
        :param path: 文件路径，可以是str或Path
        :return: None
        """
        if self._setter._downloadKit._logger is not None:
            self._setter._downloadKit._logger.record()
        self._setter._downloadKit._logger = Recorder(path)

    def print_all(self):
        """打印所有信息"""
        self._setter._downloadKit._print_mode = 'all'

    def print_failed(self):
        """只有在下载失败时打印信息"""
        self._setter._downloadKit._print_mode = 'failed'

    def print_nothing(self):
        """不打印任何信息"""
        self._setter._downloadKit._print_mode = None

    def log_all(self):
        """记录所有信息"""
        if self._setter._downloadKit._logger is None:
            raise RuntimeError('请先用log_path()设置log文件路径。')
        self._setter._downloadKit._log_mode = 'all'

    def log_failed(self):
        """只记录下载失败的信息"""
        if self._setter._downloadKit._logger is None:
            raise RuntimeError('请先用log_path()设置log文件路径。')
        self._setter._downloadKit._log_mode = 'failed'

    def log_nothing(self):
        """不进行记录"""
        self._setter._downloadKit._log_mode = None


class FileExists(object):
    """用于设置存在同名文件时处理方法"""

    def __init__(self, setter):
        """
        :param setter: Setter对象
        """
        self._setter = setter

    def __call__(self, mode):
        """设置文件存在时的处理方式
        :param mode: 'skip', 'rename', 'overwrite', 'add'
        :return: None
        """
        self._setter._downloadKit.file_exists = get_file_exists_mode(mode)

    def skip(self):
        """设为跳过"""
        self._setter._downloadKit.file_exists = 'skip'

    def rename(self):
        """设为重命名，文件名后加序号"""
        self._setter._downloadKit.file_exists = 'rename'

    def overwrite(self):
        """设为覆盖"""
        self._setter._downloadKit.file_exists = 'overwrite'

    def add(self):
        """设为追加"""
        self._setter._downloadKit.file_exists = 'add'
