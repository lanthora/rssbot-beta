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
    _format = "%(asctime)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=_format)
    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGABRT, handler)
    bot.run()


if __name__ == '__main__':
    main()
