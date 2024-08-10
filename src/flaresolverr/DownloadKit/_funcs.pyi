# -*- coding:utf-8 -*-
"""
@Author  :   g1879
@Contact :   g1879@qq.com
"""
from pathlib import Path
from threading import Lock
from typing import Union, Optional

from requests import Session, Response

FILE_EXISTS_MODE: dict = ...


def copy_session(session: Session) -> Session: ...


class BlockSizeSetter(object):
    def __set__(self, block_size, val: Union[str, int]): ...

    def __get__(self, block_size, objtype=None) -> int: ...


class PathSetter(object):
    def __set__(self, goal_path, val: Union[str, Path]): ...

    def __get__(self, goal_path, objtype=None): ...


class FileExistsSetter(object):
    def __set__(self, file_exists, mode: str): ...

    def __get__(self, file_exists, objtype=None): ...


def get_file_exists_mode(mode: str) -> str: ...


def set_charset(response: Response, encoding: Optional[str]) -> Response: ...


def get_file_info(response: Response, goal_path: str = None, rename: str = None, suffix: str = None,
                  file_exists: str = None, encoding: Optional[str] = None, lock: Lock = None) -> dict: ...


def set_session_cookies(session: Session, cookies: list) -> None: ...
