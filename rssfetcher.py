# SPDX-License-Identifier: GPL-3.0-or-later
import logging
import feedparser
from rssmodule import RSS, RSSItem


class RSSFethcer(object):
    def check_url(self, url):
        rss = RSS()
        try:
            logging.debug("请求从网络下载url")
            d = feedparser.parse(url)
            logging.debug("解析标题")
            rss.title = " ".join(d.feed.title.split())
            logging.debug("解析链接")
            rss.url = d.feed.title_detail.base
            logging.debug("解析最近文章的标题")
            _name = d.entries[0].title
            logging.debug("解析最近文章的链接")
            _link = d.entries[0].link
            logging.debug("解析最近文章的GUID")
            try:
                _guid = d.entries[0].guid
            except AttributeError:
                logging.debug("GUID不存在，使用link代替")
                _guid = _link
            logging.debug("解析完成设置标记")
            rss.mark = _guid
            logging.debug("状态设置为激活")
            rss.active = True
        except Exception:
            logging.error("生成rss过程中出现错误")
            logging.error("url: {}".format(url))
        finally:
            return rss

    def update_rss(self, url):
        try:
            rssitems = []
            d = feedparser.parse(url)
            _title = " ".join(d.feed.title.split())
            _url = d.feed.title_detail.base
            limit = len(d.entries)
            for i in range(0, limit):
                item = d.entries[i]
                _name = item.title
                _link = item.link
                try:
                    _mark = item.guid
                except AttributeError:
                    _mark = item.link
                rssitem = RSSItem(_title, _url, _name, _link, _mark)
                rssitems.append(rssitem)
            return rssitems
        except AttributeError:
            raise ParseError(url)


class ParseError(Exception):
    def __init__(self, url):
        self.url = url

    def __str__(self):
        return str('ParseError: {} could not be parsed'.format(self.url))
