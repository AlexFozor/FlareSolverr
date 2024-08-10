# -*- coding:utf-8 -*-
"""
@Author   : g1879
@Contact  : g1879@qq.com
@Copyright: (c) 2024 by g1879, Inc. All Rights Reserved.
@License  : BSD 3-Clause.
"""
from pathlib import Path
from shutil import rmtree
from threading import Lock
from time import sleep, perf_counter

from requests import Session
from websocket import WebSocketBadStatusException

from .driver import BrowserDriver, Driver
from .._configs.chromium_options import ChromiumOptions
from .._configs.session_options import SessionOptions
from .._functions.browser import connect_browser
from .._functions.cookies import CookiesList
from .._functions.settings import Settings
from .._functions.tools import PortFinder
from .._functions.tools import raise_error
from .._pages.chromium_base import Timeout
from .._pages.tabs import ChromiumTab, MixTab
from .._units.downloader import DownloadManager
from .._units.setter import BrowserSetter
from .._units.waiter import BrowserWaiter
from ..errors import BrowserConnectError, CDPError
from ..errors import PageDisconnectedError

__ERROR__ = 'error'


class Chromium(object):
    _BROWSERS = {}
    _lock = Lock()

    def __new__(cls, addr_or_opts=None, session_options=None):
        """
        :param addr_or_opts: 浏览器地址:端口、ChromiumOptions对象或端口数字（int）
        :param session_options: 使用双模Tab时使用的默认Session配置，为True使用ini文件配置
        """
        opt = handle_options(addr_or_opts)
        is_headless, browser_id, is_exists = run_browser(opt)
        with cls._lock:
            if browser_id in cls._BROWSERS:
                r = cls._BROWSERS[browser_id]
                while not hasattr(r, '_driver'):
                    sleep(.1)
                return r
        r = object.__new__(cls)
        r._chromium_options = opt
        r.is_headless = is_headless
        r._is_exists = is_exists
        r.id = browser_id
        cls._BROWSERS[browser_id] = r
        return r

    def __init__(self, addr_or_opts=None, session_options=None):
        """
        :param addr_or_opts: 浏览器地址:端口、ChromiumOptions对象或端口数字（int）
        :param session_options: 使用双模Tab时使用的默认Session配置，为True使用ini文件配置
        """
        if hasattr(self, '_created'):
            return
        self._created = True

        self._type = 'Chromium'
        self._frames = {}
        self._drivers = {}
        self._all_drivers = {}

        self._set = None
        self._wait = None
        self._timeouts = Timeout(**self._chromium_options.timeouts)
        self._load_mode = self._chromium_options.load_mode
        self._download_path = str(Path(self._chromium_options.download_path).absolute())
        self.retry_times = self._chromium_options.retry_times
        self.retry_interval = self._chromium_options.retry_interval
        self.address = self._chromium_options.address
        self._driver = BrowserDriver(self.id, 'browser', self.address, self)

        if (not self._chromium_options._ua_set and self.is_headless != self._chromium_options.is_headless) or (
                self._is_exists and self._chromium_options._new_env):
            self.quit(3, True)
            connect_browser(self._chromium_options)
            s = Session()
            s.trust_env = False
            s.keep_alive = False
            ws = s.get(f'http://{self._chromium_options.address}/json/version', headers={'Connection': 'close'})
            self.id = ws.json()['webSocketDebuggerUrl'].split('/')[-1]
            self._driver = BrowserDriver(self.id, 'browser', self.address, self)
            ws.close()
            s.close()
            self._frames = {}
            self._drivers = {}
            self._all_drivers = {}

        self.version = self._run_cdp('Browser.getVersion')['product']

        self._process_id = None
        try:
            r = self._run_cdp('SystemInfo.getProcessInfo')
            for i in r.get('processInfo', []):
                if i['type'] == 'browser':
                    self._process_id = i['id']
                    break
        except:
            pass

        self._run_cdp('Target.setDiscoverTargets', discover=True)
        self._driver.set_callback('Target.targetDestroyed', self._onTargetDestroyed)
        self._driver.set_callback('Target.targetCreated', self._onTargetCreated)
        self._dl_mgr = DownloadManager(self)

        self._session_options = SessionOptions() if session_options is True else session_options

    @property
    def user_data_path(self):
        """返回用户文件夹路径"""
        return self._chromium_options.user_data_path

    @property
    def process_id(self):
        """返回浏览器进程id"""
        return self._process_id

    @property
    def timeout(self):
        """返回timeouts设置"""
        return self._timeouts.base

    @property
    def timeouts(self):
        """返回timeouts设置"""
        return self._timeouts

    @property
    def load_mode(self):
        """返回加载模式"""
        return self._load_mode

    @property
    def download_path(self):
        """返回默认下载路径"""
        return self._download_path

    @property
    def set(self):
        if self._set is None:
            self._set = BrowserSetter(self)
        return self._set

    @property
    def wait(self):
        """返回用于等待的对象"""
        if self._wait is None:
            self._wait = BrowserWaiter(self)
        return self._wait

    @property
    def tabs_count(self):
        """返回标签页数量"""
        j = self._run_cdp('Target.getTargets')['targetInfos']  # 不要改用get，避免卡死
        return len([i for i in j if i['type'] in ('page', 'webview') and not i['url'].startswith('devtools://')])

    @property
    def tab_ids(self):
        """返回所有标签页id组成的列表"""
        j = self._driver.get(f'http://{self.address}/json').json()  # 不要改用cdp，因为顺序不对
        return [i['id'] for i in j if i['type'] in ('page', 'webview') and not i['url'].startswith('devtools://')]

    @property
    def latest_tab(self):
        """返回最新的标签页，最新标签页指最后创建或最后被激活的
        当Settings.singleton_tab_obj==True时返回Tab对象，否则返回tab id"""
        return self.get_tab(self.tab_ids[0], as_id=not Settings.singleton_tab_obj)

    def cookies(self, all_info=False):
        """以list格式返回所有域名的cookies
        :param all_info: 是否返回所有内容，False则只返回name, value, domain
        :return: cookies组成的列表
        """
        cks = self._run_cdp(f'Storage.getCookies')['cookies']
        r = cks if all_info else [{'name': c['name'], 'value': c['value'], 'domain': c['domain']} for c in cks]
        return CookiesList(r)

    def new_tab(self, url=None, new_window=False, background=False, new_context=False):
        """新建一个标签页
        :param url: 新标签页跳转到的网址
        :param new_window: 是否在新窗口打开标签页
        :param background: 是否不激活新标签页，如new_window为True则无效
        :param new_context: 是否创建新的上下文
        :return: 新标签页对象
        """
        return self._new_tab(ChromiumTab, url=url, new_window=new_window,
                             background=background, new_context=new_context)

    def new_mix_tab(self, url=None, new_window=False, background=False, new_context=False):
        """新建一个标签页
        :param url: 新标签页跳转到的网址
        :param new_window: 是否在新窗口打开标签页
        :param background: 是否不激活新标签页，如new_window为True则无效
        :param new_context: 是否创建新的上下文
        :return: 新标签页对象
        """
        return self._new_tab(MixTab, url=url, new_window=new_window,
                             background=background, new_context=new_context)

    def _new_tab(self, obj, url=None, new_window=False, background=False, new_context=False):
        """新建一个标签页
        :param obj: 要创建的Tab类型
        :param url: 新标签页跳转到的网址
        :param new_window: 是否在新窗口打开标签页
        :param background: 是否不激活新标签页，如new_window为True则无效
        :param new_context: 是否创建新的上下文
        :return: 新标签页对象
        """
        tab = None
        if new_context:
            tab = self._run_cdp('Target.createBrowserContext')['browserContextId']

        kwargs = {'url': ''}
        if new_window:
            kwargs['newWindow'] = True
        if background:
            kwargs['background'] = True
        if tab:
            kwargs['browserContextId'] = tab

        try:
            tab = self._run_cdp('Target.createTarget', **kwargs)['targetId']
        except CDPError:
            data = ('a', {'href': url or 'https://#', 'target': '_new' if new_window else '_blank'})
            tab = self.get_mix_tab() if isinstance(obj, MixTab) else self.get_tab()
            return tab.add_ele(data).click.for_new_tab(by_js=True)

        while tab not in self._drivers:
            sleep(.1)
        tab = obj(self, tab)
        if url:
            tab.get(url)
        return tab

    def get_tab(self, id_or_num=None, title=None, url=None, tab_type='page', as_id=False):
        """获取一个标签页对象，id_or_num不为None时，后面几个参数无效
        :param id_or_num: 要获取的标签页id或序号，序号从1开始，可传入负数获取倒数第几个，不是视觉排列顺序，而是激活顺序
        :param title: 要匹配title的文本，模糊匹配，为None则匹配所有
        :param url: 要匹配url的文本，模糊匹配，为None则匹配所有
        :param tab_type: tab类型，可用列表输入多个，如 'page', 'iframe' 等，为None则匹配所有
        :param as_id: 是否返回标签页id而不是标签页对象
        :return: Tab对象
        """
        return self._get_tab(id_or_num=id_or_num, title=title, url=url, tab_type=tab_type, as_id=as_id)

    def get_tabs(self, title=None, url=None, tab_type='page', as_id=False):
        """查找符合条件的tab，返回它们组成的列表，title和url是与关系
        :param title: 要匹配title的文本
        :param url: 要匹配url的文本
        :param tab_type: tab类型，可用列表输入多个
        :param as_id: 是否返回标签页id而不是标签页对象
        :return: Tab对象列表
        """
        return self._get_tabs(title=title, url=url, tab_type=tab_type, as_id=as_id)

    def get_mix_tab(self, id_or_num=None, title=None, url=None, tab_type='page', as_id=False):
        """获取一个标签页对象，id_or_num不为None时，后面几个参数无效
        :param id_or_num: 要获取的标签页id或序号，序号从1开始，可传入负数获取倒数第几个，不是视觉排列顺序，而是激活顺序
        :param title: 要匹配title的文本，模糊匹配，为None则匹配所有
        :param url: 要匹配url的文本，模糊匹配，为None则匹配所有
        :param tab_type: tab类型，可用列表输入多个，如 'page', 'iframe' 等，为None则匹配所有
        :param as_id: 是否返回标签页id而不是标签页对象
        :return: Tab对象
        """
        return self._get_tab(id_or_num=id_or_num, title=title, url=url, tab_type=tab_type, mix=True, as_id=as_id)

    def get_mix_tabs(self, title=None, url=None, tab_type='page', as_id=False):
        """查找符合条件的tab，返回它们组成的列表，title和url是与关系
        :param title: 要匹配title的文本
        :param url: 要匹配url的文本
        :param tab_type: tab类型，可用列表输入多个
        :param as_id: 是否返回标签页id而不是标签页对象
        :return: Tab对象列表
        """
        return self._get_tabs(title=title, url=url, tab_type=tab_type, mix=True, as_id=as_id)

    def _get_tab(self, id_or_num=None, title=None, url=None, tab_type='page', mix=False, as_id=False):
        """获取一个标签页对象，id_or_num不为None时，后面几个参数无效
        :param id_or_num: 要获取的标签页id或序号，序号从1开始，可传入负数获取倒数第几个，不是视觉排列顺序，而是激活顺序
        :param title: 要匹配title的文本，模糊匹配，为None则匹配所有
        :param url: 要匹配url的文本，模糊匹配，为None则匹配所有
        :param tab_type: tab类型，可用列表输入多个，如 'page', 'iframe' 等，为None则匹配所有
        :param mix: 是否返回可切换模式的Tab对象
        :param as_id: 是否返回标签页id而不是标签页对象，mix=False时无效
        :return: Tab对象
        """
        if id_or_num is not None:
            if isinstance(id_or_num, str):
                id_or_num = id_or_num
            elif isinstance(id_or_num, int):
                id_or_num = self.tab_ids[id_or_num - 1 if id_or_num > 0 else id_or_num]
            elif isinstance(id_or_num, ChromiumTab):
                return id_or_num.tab_id if as_id else ChromiumTab(self, id_or_num.tab_id)

        elif title == url is None and tab_type == 'page':
            id_or_num = self.tab_ids[0]

        else:
            tabs = self._get_tabs(title=title, url=url, tab_type=tab_type, as_id=True)
            if tabs:
                id_or_num = tabs[0]
            else:
                return None

        if as_id:
            return id_or_num
        with self._lock:
            return MixTab(self, id_or_num) if mix else ChromiumTab(self, id_or_num)

    def _get_tabs(self, title=None, url=None, tab_type='page', mix=False, as_id=False):
        """查找符合条件的tab，返回它们组成的列表，title和url是与关系
        :param title: 要匹配title的文本
        :param url: 要匹配url的文本
        :param tab_type: tab类型，可用列表输入多个
        :param mix: 是否返回可切换模式的Tab对象
        :param as_id: 是否返回标签页id而不是标签页对象，mix=False时无效
        :return: Tab对象列表
        """
        tabs = self._driver.get(f'http://{self.address}/json').json()  # 不要改用cdp

        if isinstance(tab_type, str):
            tab_type = {tab_type}
        elif isinstance(tab_type, (list, tuple, set)):
            tab_type = set(tab_type)
        elif tab_type is not None:
            raise TypeError('tab_type只能是set、list、tuple、str、None。')

        tabs = [i for i in tabs if ((title is None or title in i['title']) and (url is None or url in i['url'])
                                    and (tab_type is None or i['type'] in tab_type))]
        if as_id:
            return [tab['id'] for tab in tabs]
        with self._lock:
            if mix:
                return [MixTab(self, tab['id']) for tab in tabs]
            else:
                return [ChromiumTab(self, tab['id']) for tab in tabs]

    def close_tabs(self, tabs_or_ids=None, others=False):
        """关闭传入的标签页，默认关闭当前页。可传入多个
        :param tabs_or_ids: 要关闭的标签页对象或id，可传入列表或元组，为None时关闭最后操作的
        :param others: 是否关闭指定标签页之外的
        :return: None
        """
        all_tabs = set(self.tab_ids)
        if isinstance(tabs_or_ids, str):
            tabs = {tabs_or_ids}
        elif isinstance(tabs_or_ids, ChromiumTab):
            tabs = {tabs_or_ids.tab_id}
        elif tabs_or_ids is None:
            tabs = {self.tab_ids[0]}
        elif isinstance(tabs_or_ids, (list, tuple)):
            tabs = set(i.tab_id if isinstance(i, ChromiumTab) else i for i in tabs_or_ids)
        else:
            raise TypeError('tabs_or_ids参数只能传入标签页对象或id。')

        if others:
            tabs = all_tabs - tabs

        end_len = len(set(all_tabs) - set(tabs))
        if end_len <= 0:
            self.quit()
            return

        for tab in tabs:
            self._onTargetDestroyed(targetId=tab)
            self._driver.run('Target.closeTarget', targetId=tab)
            sleep(.2)
        end_time = perf_counter() + 3
        while self.tabs_count != end_len and perf_counter() < end_time:
            sleep(.1)

    def activate_tab(self, id_ind_tab):
        """使标签页变为活动状态
        :param id_ind_tab: 标签页id（str）、Tab对象或标签页序号（int），序号从1开始
        :return: None
        """
        if isinstance(id_ind_tab, int):
            id_ind_tab += -1 if id_ind_tab else 1
            id_ind_tab = self.tab_ids[id_ind_tab]
        elif isinstance(id_ind_tab, ChromiumTab):
            id_ind_tab = id_ind_tab.tab_id
        self._run_cdp('Target.activateTarget', targetId=id_ind_tab)

    def reconnect(self):
        """断开重连"""
        self._driver.stop()
        BrowserDriver.BROWSERS.pop(self.id)
        self._driver = BrowserDriver(self.id, 'browser', self.address, self)
        self._run_cdp('Target.setDiscoverTargets', discover=True)
        self._driver.set_callback('Target.targetDestroyed', self._onTargetDestroyed)
        self._driver.set_callback('Target.targetCreated', self._onTargetCreated)

    def quit(self, timeout=5, force=False, del_data=False):
        """关闭浏览器
        :param timeout: 等待浏览器关闭超时时间（秒）
        :param force: 是否立刻强制终止进程
        :param del_data: 是否删除用户文件夹
        :return: None
        """
        try:
            self._run_cdp('Browser.close')
        except PageDisconnectedError:
            pass
        self._driver.stop()

        drivers = list(self._all_drivers.values())
        for tab in drivers:
            for driver in tab:
                driver.stop()

        if force:
            pids = None
            try:
                pids = [pid['id'] for pid in self._run_cdp('SystemInfo.getProcessInfo')['processInfo']]
            except:
                pass

            if pids:
                from psutil import Process
                for pid in pids:
                    try:
                        Process(pid).kill()
                    except:
                        pass

                from os import popen
                from platform import system
                end_time = perf_counter() + timeout
                while perf_counter() < end_time:
                    ok = True
                    for pid in pids:
                        txt = f'tasklist | findstr {pid}' if system().lower() == 'windows' else f'ps -ef | grep {pid}'
                        p = popen(txt)
                        sleep(.05)
                        try:
                            if f'  {pid} ' in p.read():
                                ok = False
                                break
                        except TypeError:
                            pass

                    if ok:
                        break

        if del_data and not self._chromium_options.is_auto_port and self._chromium_options.user_data_path:
            path = Path(self._chromium_options.user_data_path)
            rmtree(path, True)

    def _get_driver(self, tab_id, owner=None):
        """新建并返回指定tab id的Driver
        :param tab_id: 标签页id
        :param owner: 使用该驱动的对象
        :return: Driver对象
        """
        d = self._drivers.pop(tab_id, None)
        if not d:
            d = Driver(tab_id, 'page', self.address)
        d.owner = owner
        self._all_drivers.setdefault(tab_id, set()).add(d)
        return d

    def _onTargetCreated(self, **kwargs):
        """标签页创建时执行"""
        if (kwargs['targetInfo']['type'] in ('page', 'webview')
                and kwargs['targetInfo']['targetId'] not in self._all_drivers
                and not kwargs['targetInfo']['url'].startswith('devtools://')):
            try:
                tab_id = kwargs['targetInfo']['targetId']
                d = Driver(tab_id, 'page', self.address)
                self._drivers[tab_id] = d
                self._all_drivers.setdefault(tab_id, set()).add(d)
            except WebSocketBadStatusException:
                pass

    def _onTargetDestroyed(self, **kwargs):
        """标签页关闭时执行"""
        tab_id = kwargs['targetId']
        self._dl_mgr.clear_tab_info(tab_id)
        for key in [k for k, i in self._frames.items() if i == tab_id]:
            self._frames.pop(key, None)
        for d in self._all_drivers.get(tab_id, tuple()):
            d.stop()
        self._drivers.pop(tab_id, None)
        self._all_drivers.pop(tab_id, None)

    def _run_cdp(self, cmd, **cmd_args):
        """执行Chrome DevTools Protocol语句
        :param cmd: 协议项目
        :param cmd_args: 参数
        :return: 执行的结果
        """
        ignore = cmd_args.pop('_ignore', None)
        r = self._driver.run(cmd, **cmd_args)
        return r if __ERROR__ not in r else raise_error(r, ignore)

    def _on_disconnect(self):
        Chromium._BROWSERS.pop(self.id, None)
        if self._chromium_options.is_auto_port and self._chromium_options.user_data_path:
            path = Path(self._chromium_options.user_data_path)
            end_time = perf_counter() + 7
            while perf_counter() < end_time:
                if not path.exists():
                    break
                try:
                    rmtree(path)
                    break
                except (PermissionError, FileNotFoundError, OSError):
                    pass
                sleep(.03)


def handle_options(addr_or_opts):
    """设置浏览器启动属性
    :param addr_or_opts: 'ip:port'、ChromiumOptions、Driver
    :return: 返回ChromiumOptions对象
    """
    if not addr_or_opts:
        _chromium_options = ChromiumOptions(addr_or_opts)
        if _chromium_options.is_auto_port:
            port, path = PortFinder(_chromium_options.tmp_path).get_port(_chromium_options.is_auto_port)
            _chromium_options.set_address(f'127.0.0.1:{port}')
            _chromium_options.set_user_data_path(path)
            _chromium_options.auto_port(scope=_chromium_options.is_auto_port)

    elif isinstance(addr_or_opts, ChromiumOptions):
        if addr_or_opts.is_auto_port:
            port, path = PortFinder(addr_or_opts.tmp_path).get_port(addr_or_opts.is_auto_port)
            addr_or_opts.set_address(f'127.0.0.1:{port}')
            addr_or_opts.set_user_data_path(path)
            addr_or_opts.auto_port(scope=addr_or_opts.is_auto_port)
        _chromium_options = addr_or_opts

    elif isinstance(addr_or_opts, str):
        _chromium_options = ChromiumOptions()
        _chromium_options.set_address(addr_or_opts)

    elif isinstance(addr_or_opts, int):
        _chromium_options = ChromiumOptions()
        _chromium_options.set_local_port(addr_or_opts)

    else:
        raise TypeError('只能接收ip:port格式或ChromiumOptions类型参数。')

    return _chromium_options


def run_browser(chromium_options):
    """连接浏览器"""
    is_exists = connect_browser(chromium_options)
    try:
        s = Session()
        s.trust_env = False
        s.keep_alive = False
        ws = s.get(f'http://{chromium_options.address}/json/version', headers={'Connection': 'close'})
        if not ws:
            raise BrowserConnectError('\n浏览器连接失败，请确认浏览器是否启动。')
        json = ws.json()
        browser_id = json['webSocketDebuggerUrl'].split('/')[-1]
        is_headless = 'headless' in json['User-Agent'].lower()
        ws.close()
        s.close()
    except KeyError:
        raise BrowserConnectError('浏览器版本太旧或此浏览器不支持接管。')
    except:
        raise BrowserConnectError('\n浏览器连接失败，请确认浏览器是否启动。')
    return is_headless, browser_id, is_exists
