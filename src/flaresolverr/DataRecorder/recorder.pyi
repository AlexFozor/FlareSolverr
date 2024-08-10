# -*- coding:utf-8 -*-
from typing import Any, Optional, Union

from .base import BaseRecorder
from .style.cell_style import CellStyle
from .setter import RecorderSetter


class Recorder(BaseRecorder):
    _set: RecorderSetter = ...
    _col_height: Optional[float] = ...
    _follow_styles: bool = ...
    _style: Optional[CellStyle] = ...
    _quote_char: str = ...
    _delimiter: str = ...
    _data: Union[list, dict] = ...
    data: Union[list, dict] = ...
    _head: Union[list, dict, None] = ...
    _fit_head: bool = ...
    _auto_new_col: bool = ...

    @property
    def set(self) -> RecorderSetter: ...

    @property
    def delimiter(self) -> str: ...

    @property
    def quote_char(self) -> str: ...

    def add_data(self, data: Any, table: Union[str, bool] = None) -> None: ...

    def _record(self) -> None: ...

    def _to_xlsx(self) -> None: ...

    def _to_csv(self) -> None: ...

    def _to_txt(self) -> None: ...

    def _to_json(self) -> None: ...
