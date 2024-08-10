# -*- coding:utf-8 -*-
from queue import Queue
from typing import Optional, Iterable, List

from .._pages.chromium_base import ChromiumBase


class Console(object):
    listening: bool = ...
    owner: ChromiumBase = ...
    _caught: Optional[Queue] = ...

    def __init__(self, owner: ChromiumBase) -> None: ...

    @property
    def messages(self) -> List[ConsoleData]: ...

    def start(self) -> None:
        """开启console监听"""
        ...

    def stop(self) -> None:
        """停止监听，清空已监听到的列表"""
        ...

    def clear(self) -> None:
        """清空已获取但未返回的信息"""
        ...

    def steps(self, timeout: Optional[float] = None) -> Iterable[ConsoleData]:
        """每监听到一个信息就返回，用于for循环
        :param timeout: 等待一个信息的超时时间，为None无限等待
        :return: None
        """
        ...

    def _console(self, **kwargs) -> None: ...


class ConsoleData(object):
    __slots__ = ('_data', 'source', 'level', 'text', 'url', 'line', 'column')

    def __init__(self, data: dict) -> None: ...

    def __getattr__(self, item: str) -> str: ...
