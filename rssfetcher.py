###############################################################################
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
###############################################################################
import feedparser

from rssmodule import RSS, RSSItem


class RSSFethcer(object):
    def check_url(self, url):
        # 只需要检查是否有RSS标题，文章标题，检查不通过active设为False
        rss = RSS()
        try:
            d = feedparser.parse(url)
            rss.title = d.feed.title
            rss.url = d.feed.title_detail.base
            _name = d.entries[0].title
            _link = d.entries[0].link
            rss.mark = RSSItem(name=_name, link=_link).get_mark()
            rss.active = True
        finally:
            return rss

    def update_rss(self, url):
        try:
            rssitems = []
            d = feedparser.parse(url)
            _title = d.feed.title
            _url = d.feed.title_detail.base
            for item in d.entries:
                _name = item.title
                _link = item.link
                rssitems.append(RSSItem(_title, _url, _name, _link))
            return rssitems
        except AttributeError:
            raise ParseError(url)


class ParseError(Exception):
    def __init__(self, url):
        self.url = url

    def __str__(self):
        return str('ParseError: {} could not be parsed'.format(self.url))
