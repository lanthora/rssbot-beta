#!/usr/bin/python3
import logging
import signal

import util
from rssbot import RSSBot
from rssdata import Settings

bot = RSSBot()


def handler(signal, frame):
    bot.stop()


def main():
    _level = Settings().get_log_level()
    _format = "%(asctime)s - %(message)s"
    _filename = util.absolute_path("rss.log")
    _filemode = "a"
    logging.basicConfig(level=_level, format=_format,
                        filename=_filename, filemode=_filemode)
    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGABRT, handler)
    bot.run()


if __name__ == '__main__':
    main()
