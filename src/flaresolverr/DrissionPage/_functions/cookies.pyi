# -*- coding:utf-8 -*-
"""
@Author   : g1879
@Contact  : g1879@qq.com
@Copyright: (c) 2024 by g1879, Inc. All Rights Reserved.
@License  : BSD 3-Clause.
"""
from http.cookiejar import Cookie
from typing import Union

from requests import Session
from requests.cookies import RequestsCookieJar

from .._base.browser import Chromium
from .._pages.chromium_base import ChromiumBase


def cookie_to_dict(cookie: Union[Cookie, str, dict]) -> dict: ...


def cookies_to_tuple(cookies: Union[RequestsCookieJar, list, tuple, str, dict, Cookie]) -> tuple: ...


def set_session_cookies(session: Session, cookies: Union[RequestsCookieJar, list, tuple, str, dict]) -> None: ...


def set_browser_cookies(browser: Chromium, cookies: Union[RequestsCookieJar, list, tuple, str, dict]) -> None: ...


def set_tab_cookies(page: ChromiumBase, cookies: Union[RequestsCookieJar, list, tuple, str, dict]) -> None: ...


def is_cookie_in_driver(page: ChromiumBase, cookie: dict) -> bool: ...


def format_cookie(cookie: dict) -> dict: ...


class CookiesList(list):
    def as_dict(self) -> dict: ...

    def as_str(self) -> str: ...

    def __next__(self) -> dict: ...
