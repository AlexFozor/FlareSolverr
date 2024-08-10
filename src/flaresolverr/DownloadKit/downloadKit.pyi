# -*- coding:utf-8 -*-
"""
@Author  :   g1879
@Contact :   g1879@qq.com
"""
from pathlib import Path
from queue import Queue
from threading import Lock
from typing import Union, Tuple, Any, Literal, Optional

from ..DataRecorder import Recorder
from ..DrissionPage._base.base import BasePage
from requests import Session, Response
from requests.structures import CaseInsensitiveDict

from ._funcs import FileExistsSetter, PathSetter, BlockSizeSetter
from .mission import Task, Mission, BaseTask
from .setter import Setter

FILE_EXISTS = Literal['add', 'skip', 'rename', 'overwrite', 'a', 's', 'r', 'o']


class DownloadKit(object):
    file_exists: FileExistsSetter = ...
    goal_path: PathSetter = ...
    block_size: BlockSizeSetter = ...

    _roads: int = ...
    _setter: Optional[Setter] = ...
    _print_mode: Optional[str] = ...
    _log_mode: Optional[str] = ...
    _logger: Optional[Recorder] = ...
    _retry: Optional[int] = ...
    _interval: Optional[float] = ...
    page: Optional[BasePage] = ...
    _waiting_list: Queue = ...
    _session: Session = ...
    _running_count: int = ...
    _missions_num: int = ...
    _missions: dict = ...
    _threads: dict = ...
    _timeout: Optional[int, float] = ...
    _stop_printing: bool = ...
    _lock: Lock = ...
    split: bool = ...
    _encoding: Optional[str] = ...

    def __init__(self,
                 goal_path: Union[str, Path] = None,
                 roads: int = 10,
                 driver: Union[Session, BasePage] = None,
                 file_exists: FILE_EXISTS = 'rename'): ...

    def __call__(self,
                 file_url: str,
                 goal_path: Optional[str, Path] = None,
                 rename: str = None,
                 suffix: Optional[str] = None,
                 file_exists: FILE_EXISTS = None,
                 show_msg: bool = True,
                 timeout: Optional[float] = None,
                 params: Optional[dict] = ...,
                 data: Any = ...,
                 json: Any = ...,
                 headers: Optional[dict] = ...,
                 cookies: Any = ...,
                 files: Any = ...,
                 auth: Any = ...,
                 allow_redirects: bool = ...,
                 proxies: Optional[dict] = ...,
                 hooks: Any = ...,
                 stream: Any = ...,
                 verify: Any = ...,
                 cert: Any = ...) -> tuple: ...

    @property
    def set(self) -> Setter: ...

    @property
    def roads(self) -> int: ...

    @property
    def retry(self) -> int: ...

    @property
    def interval(self) -> float: ...

    @property
    def timeout(self) -> float: ...

    @property
    def waiting_list(self) -> Queue: ...

    @property
    def session(self) -> Session: ...

    @property
    def is_running(self) -> bool: ...

    @property
    def missions(self) -> dict: ...

    @property
    def encoding(self) -> Optional[str]: ...

    def add(self,
            file_url: str,
            goal_path: Optional[str, Path] = None,
            rename: str = None,
            suffix: str = None,
            file_exists: FILE_EXISTS = None,
            split: bool = None,
            timeout: Optional[float] = None,
            params: Optional[dict] = ...,
            data: Any = None,
            json: Optional[dict, str] = ...,
            headers: Optional[dict] = ...,
            cookies: Any = ...,
            files: Any = ...,
            auth: Any = ...,
            allow_redirects: bool = ...,
            proxies: Optional[dict] = ...,
            hooks: Any = ...,
            stream: Any = ...,
            verify: Any = ...,
            cert: Any = ...) -> Mission: ...

    def download(self,
                 file_url: str,
                 goal_path: Optional[str, Path] = None,
                 rename: str = None,
                 suffix: str = None,
                 file_exists: FILE_EXISTS = None,
                 show_msg: bool = True,
                 timeout: Optional[float] = None,
                 params: Optional[dict] = ...,
                 data: Any = ...,
                 json: Any = ...,
                 headers: Optional[dict] = ...,
                 cookies: Any = ...,
                 files: Any = ...,
                 auth: Any = ...,
                 allow_redirects: bool = ...,
                 proxies: Optional[dict] = ...,
                 hooks: Any = ...,
                 stream: Any = ...,
                 verify: Any = ...,
                 cert: Any = ...) -> tuple: ...

    def _run_or_wait(self, mission: BaseTask) -> None: ...

    def _run(self, ID: int, mission: BaseTask) -> None: ...

    def get_mission(self, mission_or_id: Union[int, Mission]) -> Mission: ...

    def get_failed_missions(self) -> list: ...

    def wait(self,
             mission: Union[int, Mission] = None,
             show: bool = False,
             timeout: float = None) -> Optional[tuple]: ...

    def cancel(self) -> None: ...

    def show(self, asyn: bool = True, keep: bool = False) -> None: ...

    def _show(self, wait: float, keep: bool = False) -> None: ...

    def _connect(self, url: str, session: Session, _headers: CaseInsensitiveDict,
                 method: str, encoding: Optional[str], **kwargs) -> Tuple[Union[Response, None], str]: ...

    def _get_usable_thread(self) -> Optional[int]: ...

    def _stop_show(self) -> None: ...

    def _when_mission_done(self, mission: Mission) -> None: ...

    def _download(self,
                  mission_or_task: Union[Mission, Task],
                  thread_id: int) -> None: ...
