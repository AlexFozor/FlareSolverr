# -*- coding:utf-8 -*-
from abc import abstractmethod
from pathlib import Path
from threading import Lock
from typing import Union, Any, Optional

from .setter import OriginalSetter, BaseSetter


class OriginalRecorder(object):
    _SUPPORTS: tuple = ...
    _cache: int = ...
    _path: Optional[str] = ...
    _type: Optional[str] = ...
    _data: Union[list, dict, None] = ...
    _style_data: Union[list, dict, None] = ...
    _lock: Lock = ...
    _pause_add: bool = ...
    _pause_write: bool = ...
    show_msg: bool = ...
    _setter: Optional[OriginalSetter] = ...
    _data_count: int = ...
    _file_exists: bool = ...

    def __init__(self,
                 path: Union[str, Path, None] = None,
                 cache_size: int = None) -> None: ...

    def __del__(self) -> None: ...

    @property
    def set(self) -> OriginalSetter: ...

    @property
    def cache_size(self) -> int: ...

    @property
    def path(self) -> str: ...

    @property
    def type(self) -> str: ...

    @property
    def data(self) -> Union[dict, list]: ...

    def record(self, new_path: Union[None, str, Path] = None) -> str: ...

    def clear(self) -> None: ...

    @abstractmethod
    def add_data(self, data): ...

    @abstractmethod
    def _record(self): ...


class BaseRecorder(OriginalRecorder):
    _SUPPORTS: tuple = ...
    _encoding: str = ...
    _before: list = ...
    _after: list = ...
    _table: Optional[str] = ...
    _setter: BaseSetter = ...

    def __init__(self, path: Union[None, str, Path] = None, cache_size: int = None) -> None: ...

    @property
    def set(self) -> BaseSetter: ...

    @property
    def before(self) -> Any: ...

    @property
    def after(self) -> Any: ...

    @property
    def table(self) -> Optional[str]: ...

    @property
    def encoding(self) -> str: ...

    @abstractmethod
    def _record(self): ...
