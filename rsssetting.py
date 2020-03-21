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
import configparser
import logging
from functools import wraps

import util


def default(default_value):
    def set_default_value(fn):
        @wraps(fn)
        def decorated(*args, **kwargs):
            try:
                ret = fn(*args, **kwargs)
            except:
                ret = default_value
            finally:
                return ret
        return decorated
    return set_default_value


class settings(object):
    config = configparser.ConfigParser()
    config.read(util.absolute_path('conf.ini'))

    @classmethod
    @default("test")
    def get_noting(cls):
        return settings.config.get("default", "nothing")

    @classmethod
    def get_token(cls):
        return settings.config.get("default", "token")

    @classmethod
    @default(300)
    def get_interval(cls):
        return int(settings.config.get("default", "interval"))

    @classmethod
    @default(3)
    def get_error_limit(cls):
        return int(settings.config.get("default", "errorlimit"))

    @classmethod
    @default("lanthora")
    def get_admin(cls):
        return settings.config.get("default", "admin")

    @classmethod
    @default(0)
    def get_sublimit(cls):
        return int(settings.config.get("default", "sublimit"))

    @classmethod
    @default('<a href="https://github.com/lanthora/rssbot-beta/blob/master/README.md">README</a>')
    def get_start_msg(cls):
        return settings.config.get("default", "startmsg")

    @classmethod
    @default(logging.ERROR)
    def get_log_level(cls):
        if settings.config.get("default", "loglevel") == "DEBUG":
            return logging.DEBUG
        elif settings.config.get("default", "loglevel") == "INFO":
            return logging.INFO
        else:
            return logging.ERROR


if __name__ == "__main__":
    print(settings.get_noting())
    print(settings.get_admin())
    print(settings.get_error_limit())
    print(settings.get_start_msg())
    print(settings.get_token())
    print(settings.get_interval())
    print(settings.get_sublimit())
    print(settings.get_log_level())
