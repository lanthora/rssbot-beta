#!/usr/bin/python3
import configparser
import logging
import sys

import util
from rssbot import RSSBot
from rssdata import Settings

if __name__ == '__main__':
    _level = Settings().get_log_level()
    _format = "%(asctime)s - %(message)s"
    _filename = util.absolute_path("rss.log")
    _filemode = "a"
    logging.basicConfig(level=_level, format=_format,
                        filename=_filename, filemode=_filemode)

    bot = RSSBot()
    bot.run()
