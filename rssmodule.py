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
        return util.md5sum(self.name + self.url)
