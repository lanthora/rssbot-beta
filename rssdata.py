# SPDX-License-Identifier: GPL-3.0-or-later
import configparser
import json
import logging
import random
import time

from util import absolute_path, default, singleton


@singleton
class Settings(object):

    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read(absolute_path('conf.ini'))

    @default("test")
    def get_noting(self):
        return self.config.get("default", "nothing")

    def get_token(self):
        return self.config.get("default", "token")

    @default(300)
    def get_interval(self):
        return int(self.config.get("default", "interval"))

    @default(3)
    def get_error_limit(self):
        return int(self.config.get("default", "errorlimit"))

    @default("lanthora")
    def get_admin(self):
        return self.config.get("default", "admin")

    @default(0)
    def get_sublimit(self):
        return int(self.config.get("default", "sublimit"))

    @default('<a href="https://github.com/lanthora/rssbot-beta/blob/master/README.md">README</a>')
    def get_start_msg(self):
        return self.config.get("default", "startmsg")
