# -*- coding:utf-8 -*-
"""
@Author   : g1879
@Contact  : g1879@qq.com
@Copyright: (c) 2024 by g1879, Inc. All Rights Reserved.
@License  : BSD 3-Clause.
"""
from ._base.browser import Chromium
from ._configs.chromium_options import ChromiumOptions
from ._configs.session_options import SessionOptions
from ._pages.session_page import SessionPage

from ._pages.chromium_page import ChromiumPage
from ._pages.mix_page import MixPage
from ._pages.mix_page import MixPage as WebPage

__all__ = ['MixPage', 'WebPage', 'ChromiumPage', 'Chromium', 'ChromiumOptions', 'SessionOptions', 'SessionPage', '__version__']
__version__: str = ...
