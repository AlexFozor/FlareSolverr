# -*- coding:utf-8 -*-
"""
@Author   : g1879
@Contact  : g1879@qq.com
@Copyright: (c) 2024 by g1879, Inc. All Rights Reserved.
@License  : BSD 3-Clause.
"""
from datetime import datetime
from http.cookiejar import Cookie, CookieJar

from tldextract import extract


def cookie_to_dict(cookie):
    """把Cookie对象转为dict格式
    :param cookie: Cookie对象、字符串或字典
    :return: cookie字典
    """
    if isinstance(cookie, Cookie):
        cookie_dict = cookie.__dict__.copy()
        cookie_dict.pop('rfc2109', None)
        cookie_dict.pop('_rest', None)
        return cookie_dict

    elif isinstance(cookie, dict):
        cookie_dict = cookie

    elif isinstance(cookie, str):
        cookie_dict = {}
        for attr in cookie.strip().rstrip(';,').split(',' if ',' in cookie else ';'):
            attr_val = attr.strip().split('=', 1)
            if attr_val[0] in ('domain', 'path', 'expires', 'max-age', 'HttpOnly', 'secure', 'expiry', 'name', 'value'):
                cookie_dict[attr_val[0]] = attr_val[1] if len(attr_val) == 2 else ''
            else:
                cookie_dict['name'] = attr_val[0]
                cookie_dict['value'] = attr_val[1] if len(attr_val) == 2 else ''

        return cookie_dict

    else:
        raise TypeError('cookie参数必须为Cookie、str或dict类型。')

    return cookie_dict


def cookies_to_tuple(cookies):
    """把cookies转为tuple格式
    :param cookies: cookies信息，可为CookieJar, list, tuple, str, dict
    :return: 返回tuple形式的cookies
    """
    if isinstance(cookies, (list, tuple, CookieJar)):
        cookies = tuple(cookie_to_dict(cookie) for cookie in cookies)

    elif isinstance(cookies, str):
        c_dict = {}
        cookies = cookies.rstrip('; ')
        cookies = cookies.split(';')

        for attr in cookies:
            attr_val = attr.strip().split('=', 1)
            c_dict[attr_val[0]] = attr_val[1] if len(attr_val) == 2 else True
        cookies = _dict_cookies_to_tuple(c_dict)

    elif isinstance(cookies, dict):
        cookies = _dict_cookies_to_tuple(cookies)

    elif isinstance(cookies, Cookie):
        cookies = (cookie_to_dict(cookies),)

    else:
        raise TypeError('cookies参数必须为Cookie、CookieJar、list、tuple、str或dict类型。')

    return cookies


def set_session_cookies(session, cookies):
    """设置Session对象的cookies
    :param session: Session对象
    :param cookies: cookies信息
    :return: None
    """
    for cookie in cookies_to_tuple(cookies):
        if cookie['value'] is None:
            cookie['value'] = ''

        kwargs = {x: cookie[x] for x in cookie
                  if x.lower() in ('version', 'port', 'domain', 'path', 'secure',
                                   'expires', 'discard', 'comment', 'comment_url', 'rest')}

        if 'expiry' in cookie:
            kwargs['expires'] = cookie['expiry']

        session.cookies.set(cookie['name'], cookie['value'], **kwargs)


def set_browser_cookies(browser, cookies):
    """设置cookies值
    :param browser: 页面对象
    :param cookies: cookies信息
    :return: None
    """
    c = []
    for cookie in cookies_to_tuple(cookies):
        if 'domain' not in cookie and 'url' not in cookie:
            raise ValueError(f"cookie必须带有'domain'或'url'字段：{cookie}")
        c.append(format_cookie(cookie))
    browser._run_cdp('Storage.setCookies', cookies=c)


def set_tab_cookies(page, cookies):
    """设置cookies值
    :param page: 页面对象
    :param cookies: cookies信息
    :return: None
    """
    for cookie in cookies_to_tuple(cookies):
        cookie = format_cookie(cookie)

        if cookie['name'].startswith('__Host-'):
            if not page.url.startswith('http'):
                cookie['name'] = cookie['name'].replace('__Host-', '__Secure-', 1)
            else:
                cookie['url'] = page.url
            page._run_cdp_loaded('Network.setCookie', **cookie)
            continue  # 不用设置域名，可退出

        if cookie.get('domain', None):
            try:
                page._run_cdp_loaded('Network.setCookie', **cookie)
                if not is_cookie_in_driver(page, cookie):
                    page.browser.set.cookies(cookie)
                continue
            except Exception:
                pass

        url = page._browser_url
        if not url.startswith('http'):
            raise RuntimeError(f'未设置域名，请设置cookie的domain参数或先访问一个网站。{cookie}')
        ex_url = extract(url)
        d_list = ex_url.subdomain.split('.')
        d_list.append(f'{ex_url.domain}.{ex_url.suffix}' if ex_url.suffix else ex_url.domain)

        tmp = [d_list[0]]
        if len(d_list) > 1:
            for i in d_list[1:]:
                tmp.append('.')
                tmp.append(i)

        for i in range(len(tmp)):
            cookie['domain'] = ''.join(tmp[i:])
            page._run_cdp_loaded('Network.setCookie', **cookie)
            if is_cookie_in_driver(page, cookie):
                break


def is_cookie_in_driver(page, cookie):
    """查询cookie是否在浏览器内
    :param page: BasePage对象
    :param cookie: dict格式cookie
    :return: bool
    """
    if 'domain' in cookie:
        for c in page.cookies(all_domains=True):
            if cookie['name'] == c['name'] and cookie['value'] == c['value'] and cookie['domain'] == c.get('domain',
                                                                                                           None):
                return True
    else:
        for c in page.cookies(all_domains=True):
            if cookie['name'] == c['name'] and cookie['value'] == c['value']:
                return True
    return False


def format_cookie(cookie):
    """设置cookie为可用格式
    :param cookie: dict格式cookie
    :return: 格式化后的cookie字典
    """
    if 'expiry' in cookie:
        cookie['expires'] = int(cookie['expiry'])
        cookie.pop('expiry')

    if 'expires' in cookie:
        if not cookie['expires']:
            cookie.pop('expires')

        elif isinstance(cookie['expires'], str):
            if cookie['expires'].isdigit():
                cookie['expires'] = int(cookie['expires'])

            elif cookie['expires'].replace('.', '').isdigit():
                cookie['expires'] = float(cookie['expires'])

            else:
                try:
                    cookie['expires'] = datetime.strptime(cookie['expires'], '%a, %d %b %Y %H:%M:%S GMT').timestamp()
                except ValueError:
                    cookie['expires'] = datetime.strptime(cookie['expires'], '%a, %d %b %y %H:%M:%S GMT').timestamp()

    if cookie['value'] is None:
        cookie['value'] = ''
    elif not isinstance(cookie['value'], str):
        cookie['value'] = str(cookie['value'])

    if cookie['name'].startswith('__Host-'):
        cookie['path'] = '/'
        cookie['secure'] = True

    elif cookie['name'].startswith('__Secure-'):
        cookie['secure'] = True

    return cookie


class CookiesList(list):
    def as_dict(self):
        """以dict格式返回，只包含name和value字段"""
        return {c['name']: c['value'] for c in self}

    def as_str(self):
        """以str格式返回，只包含name和value字段"""
        return '; '.join([f'{c["name"]}={c["value"]}' for c in self])


def _dict_cookies_to_tuple(cookies: dict):
    """把dict形式的cookies转换为tuple形式
    :param cookies: 单个或多个cookies，单个时包含'name'和'value'
    :return: 多个dict格式cookies组成的列表
    """
    if 'name' in cookies and 'value' in cookies:  # 单个cookie
        return (cookies,)
    keys = ('domain', 'path', 'expires', 'max-age', 'HttpOnly', 'secure', 'expiry')
    template = {k: v for k, v in cookies.items() if k in keys}
    return tuple(dict(**{'name': k, 'value': v}, **template) for k, v in cookies.items() if k not in keys)
