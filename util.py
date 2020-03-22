# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#                                                                             #
#     Copyright (C)     2019-2020   lanthora                                  #
#                                                                             #
#    This program is free software: you can redistribute it and/or modify     #
#    it under the terms of the GNU General Public License as published by     #
#    the Free Software Foundation, either version 3 of the License, or        #
#    (at your option) any later version.                                      #
#                                                                             #
#    This program is distributed in the hope that it will be useful,          #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of           #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the            #
#    GNU General Public License for more details.                             #
#                                                                             #
#    You should have received a copy of the GNU General Public License        #
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.   #
#                                                                             #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
import hashlib
import json
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
def delete_unmatched(lines: [], regular):
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
