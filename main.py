#!/usr/bin/python3
import logging
import sys

from rssbot import RSSBot

if __name__ == '__main__':
    # 设置log等级
    _level = logging.ERROR
    _format = '%(filename)s[line:%(lineno)d]: %(message)s'
    logging.basicConfig(level=_level, format=_format)

    # 启动bot
    bot = RSSBot()
    bot.run()
