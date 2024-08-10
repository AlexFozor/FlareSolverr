# -*- coding:utf-8 -*-
"""
@Author   : g1879
@Contact  : g1879@qq.com
@Copyright: (c) 2024 by g1879, Inc. All Rights Reserved.
@License  : BSD 3-Clause.
"""
from pathlib import Path
from typing import Union, Optional, Tuple

from .._base.base import DrissionElement, BaseParser
from .._elements.chromium_element import ChromiumElement
from .._pages.chromium_base import ChromiumBase
from .._pages.chromium_page import ChromiumPage
from .._pages.tabs import ChromiumTab


def get_ele_txt(e: DrissionElement) -> str: ...


def format_html(text: str) -> str: ...


def location_in_viewport(page: ChromiumBase, loc_x: float, loc_y: float) -> bool: ...


def offset_scroll(ele: ChromiumElement, offset_x: float, offset_y: float) -> Tuple[int, int]: ...


def make_absolute_link(link: str, baseURI: str = None) -> str: ...


def is_js_func(func: str) -> bool: ...


def get_blob(page: ChromiumBase, url: str, as_bytes: bool = True) -> bytes: ...


def save_page(tab: Union[ChromiumPage, ChromiumTab],
              path: Union[Path, str, None] = None,
              name: Optional[str] = None,
              as_pdf: bool = False,
              kwargs: dict = None) -> Union[bytes, str]: ...


def get_mhtml(page: Union[ChromiumPage, ChromiumTab],
              path: Optional[Path] = None,
              name: Optional[str] = None) -> Union[bytes, str]: ...


def get_pdf(page: Union[ChromiumPage, ChromiumTab],
            path: Optional[Path] = None,
            name: Optional[str] = None,
            kwargs: dict = None) -> Union[bytes, str]: ...


def tree(ele_or_page: BaseParser,
         text: Union[int, bool] = False,
         show_js: bool = False,
         show_css: bool = False) -> None: ...


def format_headers(txt: str) -> dict: ...
