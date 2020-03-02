#!/usr/bin/python3
import logging
import sys
import configparser

from rssbot import RSSBot

if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('conf.ini')

    if config.get("default", "loglevel") == 'ERROR':
        _level = logging.ERROR
    elif config.get("default", "loglevel") == 'INFO':
        _level = logging.INFO
    else:
        _level = logging.DEBUG

    _format = "%(asctime)s - %(message)s"
    _filename = "rss.log"
    _filemode = "a"
    logging.basicConfig(level=_level, format=_format,
                        filename=_filename, filemode=_filemode)

    bot = RSSBot()
    bot.run()
