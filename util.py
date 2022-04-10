# SPDX-License-Identifier: GPL-3.0-or-later
import hashlib
import logging
import re
import sys
from functools import wraps


def md5sum(plain: str) -> str:
    hl = hashlib.md5()
    hl.update(str(plain).encode(encoding='utf-8'))
    crypt = hl.hexdigest()
    return crypt


def absolute_path(relative_path: str) -> str:
    return "{}/{}".format(sys.path[0], relative_path)


def singleton(cls):
    _instance = {}

    def inner():
        if cls not in _instance:
            _instance[cls] = cls()
        return _instance[cls]
    return inner


def default(default_value):
    def set_default_value(fn):
        @wraps(fn)
        def decorated(*args, **kwargs):
            try:
                ret = fn(*args, **kwargs)
            except:
                ret = default_value
                logging.debug("函数 {} 使用默认返回值 {}".format(
                    fn.__name__, default_value))
            finally:
                return ret
        return decorated
    return set_default_value


@default([])
def delete_unmatched(lines, regular):
    # 拆分行首的'\n'会出现lines[0]为''的情况，计数时不需要考虑第一个
    logging.debug("需要进行正则匹配的数量 {}".format(len(lines)-1))
    lines = [line for line in lines if re.match(regular, line) != None]
    logging.debug("匹配后剩余数量 {}".format(len(lines)))
    return lines


def regular_match(lines: str, regular):
    if regular == None:
        logging.debug("未设置正则匹配 直接返回")
        return lines
    lines = "\n".join(delete_unmatched(lines.split("\n"), regular))
    logging.debug("最终推送的字符串为 {}".format(lines))
    return "\n{}".format(lines)


if __name__ == '__main__':
    print(regular_match("1\n2\n3\n4", ".*"))
