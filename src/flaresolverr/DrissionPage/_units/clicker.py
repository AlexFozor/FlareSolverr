# -*- coding:utf-8 -*-
"""
@Author   : g1879
@Contact  : g1879@qq.com
@Copyright: (c) 2024 by g1879, Inc. All Rights Reserved.
@License  : BSD 3-Clause.
"""
from time import perf_counter, sleep

from .._functions.settings import Settings
from .._functions.web import offset_scroll
from ..errors import CanNotClickError, CDPError, NoRectError, AlertExistsError


class Clicker(object):
    def __init__(self, ele):
        """
        :param ele: ChromiumElement
        """
        self._ele = ele

    def __call__(self, by_js=False, timeout=1.5, wait_stop=True):
        """点击元素
        如果遇到遮挡，可选择是否用js点击
        :param by_js: 是否用js点击，为None时先用模拟点击，遇到遮挡改用js，为True时直接用js点击，为False时只用模拟点击
        :param timeout: 模拟点击的超时时间（秒），等待元素可见、可用、进入视口
        :param wait_stop: 是否等待元素运动结束再执行点击
        :return: 是否点击成功
        """
        return self.left(by_js, timeout, wait_stop)

    def left(self, by_js=False, timeout=1.5, wait_stop=True):
        """点击元素，可选择是否用js点击
        :param by_js: 是否用js点击，为None时先用模拟点击，遇到遮挡改用js，为True时直接用js点击，为False时只用模拟点击
        :param timeout: 模拟点击的超时时间（秒），等待元素可见、可用、进入视口
        :param wait_stop: 是否等待元素运动结束再执行点击
        :return: 是否点击成功
        """
        if self._ele.tag == 'option':
            if not self._ele.states.is_selected:
                self._ele.parent('t:select').select.by_option(self._ele)
            else:
                select = self._ele.parent('t:select')
                if select.select.is_multi:
                    self._ele.parent('t:select').select.cancel_by_option(self._ele)
            return self._ele

        if not by_js:  # 模拟点击
            can_click = False
            timeout = self._ele.owner.timeout if timeout is None else timeout
            rect = None
            if timeout == 0:
                try:
                    self._ele.scroll.to_see()
                    if self._ele.states.is_enabled and self._ele.states.is_displayed:
                        rect = self._ele.rect.viewport_corners
                        can_click = True
                except NoRectError:
                    if by_js is False:
                        raise

            else:
                rect = self._ele.states.has_rect
                end_time = perf_counter() + timeout
                while not rect and perf_counter() < end_time:
                    rect = self._ele.states.has_rect
                    sleep(.001)

                if wait_stop and rect:
                    self._ele.wait.stop_moving(timeout=end_time - perf_counter())
                if rect:
                    self._ele.scroll.to_see()
                    rect = self._ele.rect.corners
                    while perf_counter() < end_time:
                        if self._ele.states.is_enabled and self._ele.states.is_displayed:
                            can_click = True
                            break
                        sleep(.001)

                elif by_js is False:
                    raise NoRectError

            if can_click and not self._ele.states.is_in_viewport:
                by_js = True

            elif can_click and (by_js is False or not self._ele.states.is_covered):
                x = rect[1][0] - (rect[1][0] - rect[0][0]) / 2
                y = rect[0][0] + 3
                try:
                    r = self._ele.owner._run_cdp('DOM.getNodeForLocation', x=int(x), y=int(y),
                                                 includeUserAgentShadowDOM=True, ignorePointerEventsNone=True)
                    if r['backendNodeId'] != self._ele._backend_id:
                        vx, vy = self._ele.rect.viewport_midpoint
                    else:
                        vx, vy = self._ele.rect.viewport_click_point

                except CDPError:
                    vx, vy = self._ele.rect.viewport_midpoint

                self._click(vx, vy)
                return self._ele

        if by_js is not False:
            self._ele._run_js('this.click();')
            return self._ele
        if Settings.raise_when_click_failed:
            raise CanNotClickError
        return False

    def right(self):
        """右键单击"""
        self._ele.owner.scroll.to_see(self._ele)
        return self._click(*self._ele.rect.viewport_click_point, button='right')

    def middle(self, get_tab=True):
        """中键单击，默认返回新出现的tab对象
        :param get_tab: 是否返回新tab对象，为False则返回None
        :return: Tab对象或None
        """
        self._ele.owner.scroll.to_see(self._ele)
        curr_tid = self._ele.tab.browser.tab_ids[0]
        self._click(*self._ele.rect.viewport_click_point, button='middle')
        if get_tab:
            tid = self._ele.tab.browser.wait.new_tab(curr_tab=curr_tid)
            if not tid:
                raise RuntimeError('没有出现新标签页。')
            return (self._ele.tab.browser.get_mix_tab(tid) if self._ele.tab._type == 'MixTab'
                    else self._ele.tab.browser.get_tab(tid))

    def at(self, offset_x=None, offset_y=None, button='left', count=1):
        """带偏移量点击本元素，相对于左上角坐标。不传入x或y值时点击元素中间点
        :param offset_x: 相对元素左上角坐标的x轴偏移量
        :param offset_y: 相对元素左上角坐标的y轴偏移量
        :param button: 点击哪个键，可选 left, middle, right, back, forward
        :param count: 点击次数
        :return: None
        """
        self._ele.owner.scroll.to_see(self._ele)
        if offset_x is None and offset_y is None:
            w, h = self._ele.rect.size
            offset_x = w // 2
            offset_y = h // 2
        return self._click(*offset_scroll(self._ele, offset_x, offset_y), button=button, count=count)

    def multi(self, times=2):
        """多次点击
        :param times: 默认双击
        :return: None
        """
        return self.at(count=times)

    def to_download(self, save_path=None, rename=None, suffix=None, new_tab=False, by_js=False, timeout=None):
        """点击触发下载
        :param save_path: 保存路径，为None保存在原来设置的，如未设置保存到当前路径
        :param rename: 重命名文件名
        :param suffix: 指定文件后缀
        :param new_tab: 该下载是否在新tab中触发
        :param by_js: 是否用js方式点击，逻辑与click()一致
        :param timeout: 等待下载触发的超时时间，为None则使用页面对象设置
        :return: DownloadMission对象
        """
        if save_path:
            self._ele.tab.set.download_path(save_path)
        elif not self._ele.tab._browser._dl_mgr._running:
            self._ele.tab._browser.set.download_path('.')

        obj = self._ele.tab._browser if new_tab else self._ele.owner._tab
        if rename or suffix:
            obj.set.download_file_name(rename, suffix)

        self.left(by_js=by_js)
        return obj.wait.download_begin(timeout=timeout)

    def to_upload(self, file_paths, by_js=False):
        """触发上传文件选择框并自动填入指定路径
        :param file_paths: 文件路径，如果上传框支持多文件，可传入列表或字符串，字符串时多个文件用回车分隔
        :param by_js: 是否用js方式点击，逻辑与click()一致
        :return: None
        """
        self._ele.owner.set.upload_files(file_paths)
        self.left(by_js=by_js)
        self._ele.owner.wait.upload_paths_inputted()

    def for_new_tab(self, by_js=False, timeout=3):
        """点击后等待新tab出现并返回其对象
        :param by_js: 是否使用js点击，逻辑与click()一致
        :param timeout: 等待超时时间
        :return: 新标签页对象，如果没有等到新标签页出现则抛出异常
        """
        curr_tid = self._ele.tab.browser.tab_ids[0]
        self.left(by_js=by_js)
        tid = self._ele.tab.browser.wait.new_tab(timeout=timeout, curr_tab=curr_tid)
        if not tid:
            raise RuntimeError('没有出现新标签页。')
        return (self._ele.tab.browser.get_mix_tab(tid) if self._ele.tab._type == 'MixTab'
                else self._ele.tab.browser.get_tab(tid))

    def for_url_change(self, text=None, exclude=False, by_js=False, timeout=None):
        """点击并等待tab的url变成包含或不包含指定文本
        :param text: 用于识别的文本，为None等待当前url变化
        :param exclude: 是否排除，为True时当url不包含text指定文本时返回True，text为None时自动设为True
        :param by_js: 是否用js点击
        :param timeout: 超时时间（秒），为None使用页面设置
        :return: 是否等待成功
        """
        if text is None:
            exclude = True
            text = self._ele.tab.url
        self.left(by_js=by_js)
        return True if self._ele.tab.wait.url_change(text=text, exclude=exclude, timeout=timeout) else False

    def for_title_change(self, text=None, exclude=False, by_js=False, timeout=None):
        """点击并等待tab的title变成包含或不包含指定文本
        :param text: 用于识别的文本，为None等待当前title变化
        :param exclude: 是否排除，为True时当title不包含text指定文本时返回True，text为None时自动设为True
        :param by_js: 是否用js点击
        :param timeout: 超时时间（秒），为None使用页面设置
        :return: 是否等待成功
        """
        if text is None:
            exclude = True
            text = self._ele.tab.title
        self.left(by_js=by_js)
        return True if self._ele.tab.wait.title_change(text=text, exclude=exclude, timeout=timeout) else False

    def _click(self, view_x, view_y, button='left', count=1):
        """实施点击
        :param view_x: 视口x坐标
        :param view_y: 视口y坐标
        :param button: 'left' 'right' 'middle'  'back' 'forward'
        :param count: 点击次数
        :return: None
        """
        self._ele.owner._run_cdp('Input.dispatchMouseEvent', type='mousePressed', x=view_x,
                                 y=view_y, button=button, clickCount=count, _ignore=AlertExistsError)
        self._ele.owner._run_cdp('Input.dispatchMouseEvent', type='mouseReleased', x=view_x,
                                 y=view_y, button=button, _ignore=AlertExistsError)
        return self._ele
