# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#                                                                             #
#     Copyright (C)     2019   lanthora                                       #
#                                                                             #
#    This program is free software: you can redistribute it and/or modify     #
#    it under the terms of the GNU General Public License as published by     #
#    the Free Software Foundation, either version 3 of the License, or        #
#    (at your option) any later version.                                      #
#                                                                             #
#    This program is distributed in the hope that it will be useful,          #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of           #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the            #
#    GNU General Public License for more details.                             #
#                                                                             #
#    You should have received a copy of the GNU General Public License        #
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.   #
#                                                                             #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
import feedparser

import util
from rssmodule import RSS, RSSItem


class RSSFethcer(object):
    def check_url(self, url):
        rss = RSS()
        try:
            d = feedparser.parse(url)
            rss.title = d.feed.title
            rss.url = d.feed.title_detail.base
            _name = d.entries[0].title
            _link = d.entries[0].link
            _guid = d.entries[0].guid
            rss.mark = _guid
            rss.active = True
        finally:
            return rss

    def update_rss(self, url):
        try:
            rssitems = []
            d = feedparser.parse(url)
            _title = d.feed.title
            _url = d.feed.title_detail.base
            limit = len(d.entries)
            for i in range(0, limit):
                item = d.entries[i]
                _name = item.title
                _link = item.link
                _mark = item.guid
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
