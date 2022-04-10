# SPDX-License-Identifier: GPL-3.0-or-later


class RSS(object):
    def __init__(self, title='', url='', mark='', active=False):
        self.title = title
        self.url = url
        self.mark = mark
        self.active = active


class RSSItem(object):
    def __init__(self, title='', url='', name='', link='', mark=''):
        self.title = title
        self.url = url
        self.name = name
        self.link = link
        self.mark = mark
