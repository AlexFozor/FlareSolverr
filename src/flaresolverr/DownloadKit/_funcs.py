# -*- coding:utf-8 -*-
"""
@Author  :   g1879
@Contact :   g1879@qq.com
"""
from copy import copy
from os import path as os_PATH
from pathlib import Path
from random import randint
from re import search, sub
from time import time
from urllib.parse import unquote

from ..DataRecorder.tools import get_usable_path, make_valid_name
from requests import Session

FILE_EXISTS_MODE = {'rename': 'rename', 'overwrite': 'overwrite', 'skip': 'skip', 'add': 'add', 'r': 'rename',
                    'o': 'overwrite', 's': 'skip', 'a': 'add'}


def copy_session(session):
    """复制输入Session对象，返回一个新的
    :param session: 被复制的Session对象
    :return: 新Session对象
    """
    new = Session()
    new.headers = session.headers.copy()
    new.cookies = session.cookies.copy()
    new.stream = True
    new.auth = session.auth
    new.proxies = dict(session.proxies).copy()
    new.params = copy(session.params)  #
    new.cert = session.cert
    new.max_redirects = session.max_redirects
    new.trust_env = session.trust_env
    new.verify = session.verify

    return new


class BlockSizeSetter(object):
    def __set__(self, block_size, val):
        if isinstance(val, int) and val > 0:
            size = val
        elif isinstance(val, str):
            units = {'b': 1, 'k': 1024, 'm': 1048576, 'g': 21474836480}
            num = int(val[:-1])
            unit = units.get(val[-1].lower(), None)
            if unit and num > 0:
                size = num * unit
            else:
                raise ValueError('单位只支持B、K、M、G，数字必须为大于0的整数。')
        else:
            raise TypeError('split_size只能传入int或str，数字必须为大于0的整数。')

        block_size._block_size = size

    def __get__(self, block_size, objtype=None) -> int:
        return block_size._block_size


class PathSetter(object):
    def __set__(self, goal_path, val):
        if val is not None and not isinstance(val, (str, Path)):
            raise TypeError('goal_path只能是str或Path类型。')
        goal_path._goal_path = str(val) if isinstance(val, Path) else val

    def __get__(self, goal_path, objtype=None):
        return goal_path._goal_path


class FileExistsSetter(object):
    def __set__(self, file_exists, mode):
        file_exists._file_exists = get_file_exists_mode(mode)

    def __get__(self, file_exists, objtype=None):
        return file_exists._file_exists


def get_file_exists_mode(mode):
    """获取文件重名时处理策略名称
    :param mode: 输入
    :return: 标准字符串
    """
    mode = FILE_EXISTS_MODE.get(mode, mode)
    if mode not in FILE_EXISTS_MODE:
        raise ValueError(f'''mode参数只能是 '{"', '".join(FILE_EXISTS_MODE.keys())}' 之一，现在是：{mode}''')
    return mode


def set_charset(response, encoding):
    """设置Response对象的编码
    :param response: Response对象
    :param encoding: 指定的编码格式
    :return: 设置编码后的Response对象
    """
    if encoding:
        response.encoding = encoding
        return response

    # 在headers中获取编码
    content_type = response.headers.get('content-type', '').lower()
    if not content_type.endswith(';'):
        content_type += ';'
    charset = search(r'charset[=: ]*(.*)?;?', content_type)

    if charset:
        response.encoding = charset.group(1)

    # 在headers中获取不到编码，且如果是网页
    elif content_type.replace(' ', '').startswith('text/html'):
        re_result = search(b'<meta.*?charset=[ \\\'"]*([^"\\\' />]+).*?>', response.content)

        if re_result:
            charset = re_result.group(1).decode()
        else:
            charset = response.apparent_encoding

        response.encoding = charset

    return response


def get_file_info(response, goal_path=None, rename=None, suffix=None, file_exists=None, encoding=None, lock=None):
    """获取文件信息，大小单位为byte
    包括：size、path、skip
    :param response: Response对象
    :param goal_path: 目标文件夹
    :param rename: 重命名
    :param suffix: 重命名后缀名
    :param file_exists: 存在重名文件时的处理方式
    :param encoding: 编码格式
    :param lock: 线程锁
    :return: 文件名、文件大小、保存路径、是否跳过
    """
    # ------------获取文件大小------------
    file_size = response.headers.get('Content-Length', None)
    file_size = None if file_size is None else int(file_size)

    # ------------获取网络文件名------------
    file_name = _get_file_name(response, encoding)

    # ------------获取保存路径------------
    goal_Path = Path(goal_path)
    # 按windows规则去除路径中的非法字符
    g = goal_path[len(goal_Path.anchor):] if goal_path.lower().startswith(goal_Path.anchor.lower()) else goal_path
    goal_path = goal_Path.anchor + sub(r'[*:|<>?"]', '', g).strip()
    goal_Path = Path(goal_path).absolute()
    goal_Path.mkdir(parents=True, exist_ok=True)

    # ------------获取保存文件名------------
    # -------------------重命名-------------------
    if rename:
        if suffix is not None:
            full_name = f'{rename}.{suffix}' if suffix else rename

        else:
            tmp = file_name.rsplit('.', 1)
            ext_name = f'.{tmp[-1]}' if len(tmp) > 1 else ''
            tmp = rename.rsplit('.', 1)
            ext_rename = f'.{tmp[-1]}' if len(tmp) > 1 else ''
            full_name = rename if ext_rename == ext_name else f'{rename}{ext_name}'

    elif suffix is not None:
        full_name = file_name.rsplit(".", 1)[0]
        if suffix:
            full_name = f'{full_name}.{suffix}'

    else:
        full_name = file_name

    full_name = make_valid_name(full_name)

    # -------------------生成路径-------------------
    skip = False
    create = True
    full_path = goal_Path / full_name

    with lock:
        if full_path.exists():
            if file_exists == 'rename':
                full_path = get_usable_path(full_path)

            elif file_exists == 'skip':
                skip = True
                create = False

            elif file_exists == 'overwrite':
                full_path.unlink()

            elif file_exists == 'add':
                create = False

        if create:
            with open(full_path, 'wb'):
                pass

    return {'size': file_size,
            'path': full_path,
            'skip': skip}


def _get_file_name(response, encoding) -> str:
    """从headers或url中获取文件名，如果获取不到，生成一个随机文件名
    :param response: 返回的response
    :param encoding: 在headers获取时指定编码格式
    :return: 下载文件的文件名
    """
    file_name = ''
    charset = ''
    content_disposition = response.headers.get('content-disposition', '').replace(' ', '')

    # 使用header里的文件名
    if content_disposition:
        txt = search(r'filename\*="?([^";]+)', content_disposition)
        if txt:  # 文件名自带编码方式
            txt = txt.group(1).split("''", 1)
            if len(txt) == 2:
                charset, file_name = txt
            else:
                file_name = txt[0]

        else:  # 文件名没带编码方式
            txt = search(r'filename="?([^";]+)', content_disposition)
            if txt:
                file_name = txt.group(1)

                # 获取编码（如有）
                charset = encoding or response.encoding

        file_name = file_name.strip("'")

    # 在url里获取文件名
    if not file_name and os_PATH.basename(response.url):
        file_name = os_PATH.basename(response.url).split("?")[0]

    # 找不到则用时间和随机数生成文件名
    if not file_name:
        file_name = f'untitled_{time()}_{randint(0, 100)}'

    # 去除非法字符
    charset = charset or 'utf-8'
    return unquote(file_name, charset)


def set_session_cookies(session, cookies):
    """设置Session对象的cookies
    :param session: Session对象
    :param cookies: cookies信息
    :return: None
    """
    # cookies = cookies_to_tuple(cookies)
    for cookie in cookies:
        if cookie['value'] is None:
            cookie['value'] = ''

        kwargs = {x: cookie[x] for x in cookie
                  if x.lower() in ('version', 'port', 'domain', 'path', 'secure',
                                   'expires', 'discard', 'comment', 'comment_url', 'rest')}

        if 'expiry' in cookie:
            kwargs['expires'] = cookie['expiry']

        session.cookies.set(cookie['name'], cookie['value'], **kwargs)
