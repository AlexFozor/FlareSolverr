# -*- coding:utf-8 -*-
"""
@Author   : g1879
@Contact  : g1879@qq.com
@Copyright: (c) 2024 by g1879, Inc. All Rights Reserved.
@License  : BSD 3-Clause.
"""
from pathlib import Path
from typing import Union, Tuple, Any, Optional

from requests import Session, Response

from .chromium_base import ChromiumBase
from .chromium_frame import ChromiumFrame
from .session_page import SessionPage
from .._base.browser import Chromium
from .._elements.chromium_element import ChromiumElement
from .._elements.session_element import SessionElement
from .._functions.cookies import CookiesList
from .._functions.elements import SessionElementsList, ChromiumElementsList
from .._units.rect import TabRect
from .._units.setter import TabSetter, MixTabSetter
from .._units.waiter import TabWaiter


class ChromiumTab(ChromiumBase):
    _TABS: dict = ...

    def __new__(cls, browser: Chromium, tab_id: str): ...

    def __init__(self, browser: Chromium, tab_id: str):
        self._tab: ChromiumTab = ...
        self._rect: Optional[TabRect] = ...

    def _d_set_runtime_settings(self) -> None: ...

    def close(self) -> None: ...

    @property
    def set(self) -> TabSetter: ...

    @property
    def wait(self) -> TabWaiter: ...

    def save(self,
             path: Union[str, Path] = None,
             name: str = None,
             as_pdf: bool = False,
             landscape: bool = ...,
             displayHeaderFooter: bool = ...,
             printBackground: bool = ...,
             scale: float = ...,
             paperWidth: float = ...,
             paperHeight: float = ...,
             marginTop: float = ...,
             marginBottom: float = ...,
             marginLeft: float = ...,
             marginRight: float = ...,
             pageRanges: str = ...,
             headerTemplate: str = ...,
             footerTemplate: str = ...,
             preferCSSPageSize: bool = ...,
             generateTaggedPDF: bool = ...,
             generateDocumentOutline: bool = ...) -> Union[bytes, str]: ...


class MixTab(SessionPage, ChromiumTab):
    _tab: MixTab = ...
    _mode: str = ...
    _has_driver: bool = ...
    _has_session: bool = ...

    def __init__(self, browser: Chromium, tab_id: str): ...

    def __call__(self,
                 locator: Union[Tuple[str, str], str, ChromiumElement, SessionElement],
                 index: int = 1,
                 timeout: float = None) -> Union[ChromiumElement, SessionElement]: ...

    @property
    def url(self) -> Union[str, None]: ...

    @property
    def _browser_url(self) -> Union[str, None]: ...

    @property
    def title(self) -> str: ...

    @property
    def raw_data(self) -> Union[str, bytes]: ...

    @property
    def html(self) -> str: ...

    @property
    def json(self) -> dict: ...

    @property
    def response(self) -> Response: ...

    @property
    def mode(self) -> str: ...

    @property
    def user_agent(self) -> str: ...

    @property
    def session(self) -> Session: ...

    @property
    def _session_url(self) -> str: ...

    @property
    def timeout(self) -> float: ...

    def get(self,
            url: str,
            show_errmsg: bool = False,
            retry: int | None = None,
            interval: float | None = None,
            timeout: float | None = None,
            params: dict | None = ...,
            data: Union[dict, str, None] = ...,
            json: Union[dict, str, None] = ...,
            headers: dict | None = ...,
            cookies: Any | None = ...,
            files: Any | None = ...,
            auth: Any | None = ...,
            allow_redirects: bool = ...,
            proxies: dict | None = ...,
            hooks: Any | None = ...,
            stream: Any | None = ...,
            verify: Any | None = ...,
            cert: Any | None = ...) -> Union[bool, None]: ...

    def ele(self,
            locator: Union[Tuple[str, str], str, ChromiumElement, SessionElement],
            index: int = 1,
            timeout: float = None) -> Union[ChromiumElement, SessionElement]: ...

    def eles(self,
             locator: Union[Tuple[str, str], str],
             timeout: float = None) -> Union[SessionElementsList, ChromiumElementsList]: ...

    def s_ele(self,
              locator: Union[Tuple[str, str], str] = None,
              index: int = 1) -> SessionElement: ...

    def s_eles(self, locator: Union[Tuple[str, str], str]) -> SessionElementsList: ...

    def change_mode(self, mode: str = None, go: bool = True, copy_cookies: bool = True) -> None: ...

    def cookies_to_session(self, copy_user_agent: bool = True) -> None: ...

    def cookies_to_browser(self) -> None: ...

    def cookies(self, all_domains: bool = False, all_info: bool = False) -> CookiesList: ...

    def close(self) -> None: ...

    # ----------------重写SessionPage的函数-----------------------
    def post(self,
             url: str,
             data: Union[dict, str, None] = None,
             show_errmsg: bool = False,
             retry: int | None = None,
             interval: float | None = None,
             timeout: float | None = ...,
             params: dict | None = ...,
             json: Union[dict, str, None] = ...,
             headers: dict | None = ...,
             cookies: Any | None = ...,
             files: Any | None = ...,
             auth: Any | None = ...,
             allow_redirects: bool = ...,
             proxies: dict | None = ...,
             hooks: Any | None = ...,
             stream: Any | None = ...,
             verify: Any | None = ...,
             cert: Any | None = ...) -> Union[bool, Response]: ...

    @property
    def set(self) -> MixTabSetter: ...

    def _find_elements(self,
                       locator: Union[Tuple[str, str], str, ChromiumElement, SessionElement, ChromiumFrame],
                       timeout: float = None,
                       index: Optional[int] = 1,
                       relative: bool = False,
                       raise_err: bool = None) \
            -> Union[ChromiumElement, SessionElement, ChromiumFrame, SessionElementsList, ChromiumElementsList]: ...
