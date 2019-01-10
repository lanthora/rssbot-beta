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
import util


class RSS(object):
    def __init__(self, title='', url='', mark='', active=False):
        self.title = title
        self.url = url
        self.mark = mark
        self.active = active


class RSSItem(object):
    def __init__(self, title='', url='', name='', link=''):
        self.title = title
        self.url = url
        self.name = name
        self.link = link

    def get_mark(self):
        return util.md5sum(self.name + self.link)


if __name__ == "__main__":
    import feedparser
    rss = RSS()
    url = 'https://blog.lanthora.org/atom.xml'
    d = feedparser.parse(url)
    rss.title = d.feed.title
    rss.url = d.feed.title_detail.base
    _name = d.entries[0].title
    _link = d.entries[0].link
    rss.mark = RSSItem(name=_name, link=_link).get_mark()
    print(type(rss.mark))
