#!/usr/bin/python3
import configparser
import logging
import sys

import util
from rssbot import RSSBot

if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read(util.absolute_path('conf.ini'))

    if config.get("default", "loglevel") == 'ERROR':
        _level = logging.ERROR
    elif config.get("default", "loglevel") == 'INFO':
        _level = logging.INFO
    else:
        _level = logging.DEBUG

    _format = "%(asctime)s - %(message)s"
    _filename = util.absolute_path("rss.log")
    _filemode = "a"
    logging.basicConfig(level=_level, format=_format,
                        filename=_filename, filemode=_filemode)

    bot = RSSBot()
    bot.run()
