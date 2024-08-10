# -*- coding:utf-8 -*-
"""
@Author   : g1879
@Contact  : g1879@qq.com
@Copyright: (c) 2024 by g1879, Inc. All Rights Reserved.
@License  : BSD 3-Clause.
"""
from time import sleep

from .._base.browser import Chromium
from .._functions.web import save_page
from .._pages.chromium_base import ChromiumBase
from .._units.setter import ChromiumPageSetter
from .._units.waiter import PageWaiter


class ChromiumPage(ChromiumBase):
    """用于管理浏览器的类"""
    _PAGES = {}

    def __new__(cls, addr_or_opts=None, tab_id=None, timeout=None):
        """
        :param addr_or_opts: 浏览器地址:端口、ChromiumOptions对象或端口数字（int）
        :param tab_id: 要控制的标签页id，不指定默认为激活的
        :param timeout: 超时时间（秒）
        """
        browser = Chromium(addr_or_opts=addr_or_opts)
        if browser.id in cls._PAGES:
            r = cls._PAGES[browser.id]
            while not hasattr(r, '_frame_id'):
                sleep(.1)
            return r

        r = object.__new__(cls)
        r._browser = browser
        cls._PAGES[browser.id] = r
        return r

    def __init__(self, addr_or_opts=None, tab_id=None, timeout=None):
        """
        :param addr_or_opts: 浏览器地址:端口、ChromiumOptions对象或端口数字（int）
        :param tab_id: 要控制的标签页id，不指定默认为激活的
        :param timeout: 超时时间（秒）
        """
        if hasattr(self, '_created'):
            return
        self._created = True

        self.tab = self
        super().__init__(self.browser, tab_id)
        self._type = 'ChromiumPage'
        self.set.timeouts(base=timeout)
        self._tab = self

    def _d_set_runtime_settings(self):
        """设置运行时用到的属性"""
        self._timeouts = self.browser.timeouts
        self._load_mode = self.browser._load_mode
        self._download_path = self.browser.download_path
        self.retry_times = self.browser.retry_times
        self.retry_interval = self.browser.retry_interval

    @property
    def set(self):
        """返回用于设置的对象"""
        if self._set is None:
            self._set = ChromiumPageSetter(self)
        return self._set

    @property
    def wait(self):
        """返回用于等待的对象"""
        if self._wait is None:
            self._wait = PageWaiter(self)
        return self._wait

    # ----------挂件----------

    @property
    def browser(self):
        """返回用于控制浏览器cdp的driver"""
        return self._browser

    @property
    def tabs_count(self):
        """返回标签页数量"""
        return self.browser.tabs_count

    @property
    def tab_ids(self):
        """返回所有标签页id组成的列表"""
        return self.browser.tab_ids

    @property
    def latest_tab(self):
        """返回最新的标签页，最新标签页指最后创建或最后被激活的
        当Settings.singleton_tab_obj==True时返回Tab对象，否则返回tab id"""
        return self.browser.latest_tab

    @property
    def process_id(self):
        """返回浏览器进程id"""
        return self.browser.process_id

    @property
    def browser_version(self):
        """返回所控制的浏览器版本号"""
        return self._browser.version

    @property
    def address(self):
        """返回浏览器地址ip:port"""
        return self.browser.address

    def save(self, path=None, name=None, as_pdf=False, **kwargs):
        """把当前页面保存为文件，如果path和name参数都为None，只返回文本
        :param path: 保存路径，为None且name不为None时保存在当前路径
        :param name: 文件名，为None且path不为None时用title属性值
        :param as_pdf: 为Ture保存为pdf，否则为mhtml且忽略kwargs参数
        :param kwargs: pdf生成参数
        :return: as_pdf为True时返回bytes，否则返回文件文本
        """
        return save_page(self, path, name, as_pdf, kwargs)

    def get_tab(self, id_or_num=None, title=None, url=None, tab_type='page', as_id=False):
        """获取一个标签页对象，id_or_num不为None时，后面几个参数无效
        :param id_or_num: 要获取的标签页id或序号，序号从1开始，可传入负数获取倒数第几个，不是视觉排列顺序，而是激活顺序
        :param title: 要匹配title的文本，模糊匹配，为None则匹配所有
        :param url: 要匹配url的文本，模糊匹配，为None则匹配所有
        :param tab_type: tab类型，可用列表输入多个，如 'page', 'iframe' 等，为None则匹配所有
        :param as_id: 是否返回标签页id而不是标签页对象
        :return: ChromiumTab对象
        """
        return self.browser.get_tab(id_or_num=id_or_num, title=title, url=url, tab_type=tab_type, as_id=as_id)

    def get_tabs(self, title=None, url=None, tab_type='page', as_id=False):
        """查找符合条件的tab，返回它们组成的列表
        :param title: 要匹配title的文本，模糊匹配，为None则匹配所有
        :param url: 要匹配url的文本，模糊匹配，为None则匹配所有
        :param tab_type: tab类型，可用列表输入多个，如 'page', 'iframe' 等，为None则匹配所有
        :param as_id: 是否返回标签页id而不是标签页对象
        :return: ChromiumTab对象组成的列表
        """
        return self.browser.get_tabs(title=title, url=url, tab_type=tab_type, as_id=as_id)

    def new_tab(self, url=None, new_window=False, background=False, new_context=False):
        """新建一个标签页
        :param url: 新标签页跳转到的网址
        :param new_window: 是否在新窗口打开标签页
        :param background: 是否不激活新标签页，如new_window为True则无效
        :param new_context: 是否创建新的上下文
        :return: 新标签页对象
        """
        return self.browser.new_tab(url=url, new_window=new_window, background=background, new_context=new_context)

    def activate_tab(self, id_ind_tab):
        """使标签页变为活动状态
        :param id_ind_tab: 标签页id（str）、Tab对象或标签页序号（int），序号从1开始
        :return: None
        """
        self.browser.activate_tab(id_ind_tab)

    def close(self):
        """关闭Page管理的标签页"""
        self.close_tabs(self.tab_id)

    def close_tabs(self, tabs_or_ids=None, others=False):
        """关闭传入的标签页，默认关闭当前页。可传入多个
        :param tabs_or_ids: 要关闭的标签页对象或id，可传入列表或元组，为None时关闭当前页
        :param others: 是否关闭指定标签页之外的
        :return: None
        """
        self.browser.close_tabs(tabs_or_ids=tabs_or_ids or self.tab_id, others=others)

    def quit(self, timeout=5, force=True, del_data=False):
        """关闭浏览器
        :param timeout: 等待浏览器关闭超时时间（秒）
        :param force: 关闭超时是否强制终止进程
        :param del_data: 是否删除用户文件夹
        :return: None
        """
        self.browser.quit(timeout, force, del_data=del_data)

    def _on_disconnect(self):
        """浏览器退出时执行"""
        ChromiumPage._PAGES.pop(self._browser.id, None)

    def __repr__(self):
        return f'<ChromiumPage browser_id={self.browser.id} tab_id={self.tab_id}>'
