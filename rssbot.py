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
import configparser
import logging
import threading
import time
import util

from telegram import Bot
from telegram.error import BadRequest, Unauthorized
from telegram.ext import CommandHandler, Job, Updater

from rssdatabase import RSSdatabase
from rssfetcher import ParseError, RSSFethcer
from util import RecentlyUsedElements


class RSSBot(object):
    def __init__(self):
        self.__config = configparser.ConfigParser()
        self.__config.read('conf.ini')

        self.bot = Bot(self.__config.get("default", "token"))
        self.updater = Updater(token=self.__config.get("default", "token"))
        self.dp = self.updater.dispatcher
        self.jq = self.updater.job_queue
        self.freq = int(self.__config.get("default", "freq"))

        self.fether = RSSFethcer()
        self.database = RSSdatabase()

        self.et = {}
        self.el = self.__config.get("default", "errorlimit")

        self.recently_used_elements = RecentlyUsedElements()

    def __send_html(self, chat_id, text):
        self.bot.send_message(
            chat_id, text,
            parse_mode='HTML',
            disable_web_page_preview=True
        )

    def __can_sub(self, chat_id, username):
        admin = self.__config.get("default", "admin")
        sublimit = int(self.__config.get("default", "sublimit"))
        current_sub = len(self.database.get_rss_list_by_chat_id(chat_id))
        if username == admin or current_sub < sublimit:
            return True
        else:
            return False

    def __error(self, bot, update, error):
        try:
            raise error
        except BaseException as e:
            logging.error(e)

    def __refresh(self, bot, job):
        rss_list = self.database.get_rss_list_by_chat_id()
        if len(rss_list) == 0:
            return
        delta = self.freq/len(rss_list)
        for rss in rss_list:
            threading.Thread(target=self.__update, args=(rss.url,)).start()
            time.sleep(delta)

    def __update(self, url):
        try:
            chats = self.database.get_chats_by_url(url)
            mark = self.database.get_mark(url)
            _rssitems = self.fether.update_rss(url)
            self.database.set_mark(url, _rssitems[0].mark)
            rssitems = []
            normal = False
            for rssitem in _rssitems:
                iid = util.md5sum(rssitem.url + rssitem.mark)
                if rssitem.mark == mark:
                    normal = True
                    break
                elif self.recently_used_elements.has_element(iid):
                    continue
                else:
                    rssitems.append(rssitem)
            if not normal:
                rssitems.clear()
            self.et[url] = 0
            self.__send(rssitems, chats)

        except ParseError:
            self.et[url] = self.et.setdefault(url, 0) + 1
            if self.et[url] >= int(self.el):
                self.database.set_active(url, False)
                title = self.database.get_rss_by_url(url).title
                text = '<a href="{}">{} </a>'.format(url, title)
                text += '更新时出现错误，已停止推送，请检查无误后重新订阅'
                for chat_id in chats:
                    self.__send_html(chat_id, text)

    def __send(self, rssitems, chats):
        while len(rssitems):
            rssitem = rssitems.pop()
            _text = '<b>{}</b>\n<a href="{}">{}</a>'
            text = _text.format(rssitem.title, rssitem.link, rssitem.name)
            for chat_id in chats:
                try:
                    self.__send_html(chat_id, text)
                except (BadRequest, Unauthorized):
                    self.database.del_sub('', chat_id)

    def start(self, bot, update):
        chat_id = update.message.chat_id
        text = self.__config.get("default", "startmsg")
        self.__send_html(chat_id, text)

    def subscribe(self, bot, update):
        chat_id = update.message.chat_id
        username = update.effective_user.username
        if not self.__can_sub(chat_id, username):
            text = '达到订阅数上限'
            self.__send_html(chat_id, text)
            return
        try:
            url = update.message.text.split(' ')[1]
            rss = self.fether.check_url(url)
            if rss.active:
                self.database.add_rss(rss)
                self.database.add_sub(rss.url, chat_id)
                _text = '已订阅: <a href="{}">{}</a>'
                text = _text.format(rss.url, rss.title)
            else:
                text = '暂不支持此RSS'
        except IndexError:
            text = '请输入正确的格式:\n/sub url'
        finally:
            self.__send_html(chat_id, text)

    def unsubscribe(self, bot, update):
        chat_id = update.message.chat_id
        try:
            url = update.message.text.split(' ')[1]
            name = self.database.get_rss_by_url(url).title
            self.database.del_sub(url, chat_id)
            text = '已退订: <a href="{}">{}</a>'.format(url, name)
        except IndexError:
            text = '请输入正确的格式:\n/unsub url'
        except (TypeError, AttributeError):
            text = '无此订阅'
        finally:
            self.__send_html(chat_id, text)

    def rss(self, bot, update):
        chat_id = update.message.chat_id
        rss_list = self.database.get_rss_list_by_chat_id(chat_id)
        text = '<b>你的订阅:</b>\n'
        active_rss = '▫️<a href="{}">{}</a>\n'
        inactive_rss = '▪️<a href="{}">{}</a>\n'
        if len(rss_list) == 0:
            text = '暂无订阅'
        else:
            for rss in rss_list:
                if rss.active == True:
                    text += active_rss.format(rss.url, rss.title)
                else:
                    text += inactive_rss.format(rss.url, rss.title)
        self.__send_html(chat_id, text)

    def run(self):
        self.dp.add_handler(CommandHandler('start', self.start))
        self.dp.add_handler(CommandHandler('sub', self.subscribe))
        self.dp.add_handler(CommandHandler('unsub', self.unsubscribe))
        self.dp.add_handler(CommandHandler('rss', self.rss))
        self.dp.add_error_handler(self.__error)
        self.jq.run_repeating(self.__refresh, self.freq, first=5)
        self.jq.start()
        self.updater.start_polling()
