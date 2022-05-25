# SPDX-License-Identifier: GPL-3.0-or-later
import logging
import feedparser
from rssmodule import RSS, RSSItem


class RSSFethcer(object):
    def check_url(self, url):
        rss = RSS()
        try:
            # TODO: 拆分下载和解析,并设置下载超时时间
            d = feedparser.parse(url)
            rss.title = " ".join(d.feed.title.split())
            rss.url = d.feed.title_detail.base
            _name = d.entries[0].title
            _link = d.entries[0].link
            try:
                _guid = d.entries[0].guid
            except AttributeError:
                _guid = _link
            rss.mark = _guid
            rss.active = True
        except Exception:
            logging.error("check_url failed: {}".format(url))
        finally:
            return rss

    def update_rss(self, url):
        try:
            rssitems = []
            # TODO: 拆分下载和解析,并设置下载超时时间
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
