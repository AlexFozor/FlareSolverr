# -*- coding:utf-8 -*-
from pathlib import Path
from typing import Union, Tuple, Any, Optional

from openpyxl.worksheet.worksheet import Worksheet

from .base import BaseRecorder
from .filler import Filler
from .recorder import Recorder


def align_csv(path: Union[str, Path], encoding: str = 'utf-8', delimiter: str = ',', quotechar: str = '"') -> None: ...


def get_usable_path(path: Union[str, Path], is_file: bool = True, parents: bool = True) -> Path: ...


def make_valid_name(full_name: str) -> str: ...


def get_long(txt) -> int: ...


def parse_coord(coord: Union[int, str, list, tuple, None] = None, data_col: int = None) -> Tuple[
    Optional[int], int]: ...


def process_content(content: Any, excel: bool = False) -> Union[None, int, str, float]: ...


def ok_list(data_list: Union[list, dict], excel: bool = False, as_str: bool = False) -> list: ...


def get_usable_coord_int(coord: Union[tuple, list],
                         max_row: int,
                         max_col: Union[int, Worksheet]) -> Tuple[int, int]: ...


def get_usable_coord(coord: Union[tuple, list],
                     max_row: int,
                     ws: Worksheet) -> Tuple[int, int]: ...


def data_to_list_or_dict_simplify(data: Union[list, tuple, dict, None]) -> Union[list, dict]: ...


def data_to_list_or_dict(recorder: BaseRecorder, data: Union[list, tuple, dict, None]) -> Union[list, dict]: ...


def get_csv_head(recorder: Union[Recorder, Filler], is_filler: bool = False) -> Optional[list]: ...


def get_xlsx_head(recorder: Union[Recorder, Filler], new_file: bool, new_sheet: bool,
                  first_data: Union[dict, list, tuple], ws: Worksheet, is_filler: bool = False) -> Tuple[int, bool]: ...


def create_csv(recorder: Union[Recorder, Filler]) -> None: ...


def get_wb(recorder: Union[Recorder, Filler]) -> tuple: ...


def get_ws(wb, table, tables, new_file) -> Tuple[Worksheet, bool]: ...


class FillerDict(dict):
    row: int = ...


class FillerList(list):
    row: int = ...
