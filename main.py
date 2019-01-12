#!/usr/bin/python3
import logging
import sys

from rssbot import RSSBot

if __name__ == '__main__':
    _level = logging.INFO
    _format = '%(filename)s[line:%(lineno)d]: %(message)s'
    logging.basicConfig(level=_level, format=_format)

    bot = RSSBot()
    bot.run()
