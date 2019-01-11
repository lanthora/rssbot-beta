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
import configparser
import logging
import threading
import time

from telegram import Bot
from telegram.error import BadRequest, Unauthorized
from telegram.ext import CommandHandler, Job, Updater

from rssdatabase import RSSdatabase
from rssfetcher import ParseError, RSSFethcer


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

        # error times
        self.et = {}
        # error limit
        self.el = self.__config.get("default", "errorlimit")

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
            self.database.set_mark(url, _rssitems[0].get_mark())
            rssitems = []
            for rssitem in _rssitems:
                if rssitem.get_mark() == mark:
                    break
                else:
                    rssitems.append(rssitem)
            self.et[url] = 0
            self.__send(rssitems, chats)

        except ParseError:
            self.et[url] = self.et.setdefault(url, 0) + 1
            if self.et[url] > int(self.el):
                self.database.set_active(url, False)
                title = self.database.get_rss_by_url(url).title
                text = '<a href="{}">{} </a>'.format(url, title)
                text += 'An exception occurred in the parsing, '
                text += 'the push has stopped, please check and resubscribe.'
                for chat_id in chats:
                    self.__send_html(chat_id, text)

    def __send(self, rssitems, chats):
        for rssitem in rssitems:
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
            text = 'Reach the subscription limit.'
            self.__send_html(chat_id, text)
            return
        try:
            url = update.message.text.split(' ')[1]
            rss = self.fether.check_url(url)
            if rss.active:
                self.database.add_rss(rss)
                self.database.add_sub(rss.url, chat_id)
                _text = 'Subscribed: <a href="{}">{}</a>.'
                text = _text.format(rss.url, rss.title)
            else:
                text = 'Temporarily does not support this kind of RSS, please open issue or push request.'
        except IndexError:
            text = 'Please enter the correct format:\n/sub url'
        finally:
            self.__send_html(chat_id, text)

    def unsubscribe(self, bot, update):
        chat_id = update.message.chat_id
        try:
            url = update.message.text.split(' ')[1]
            name = self.database.get_rss_by_url(url).title
            self.database.del_sub(url, chat_id)
            text = 'Unsubscribed: <a href="{}">{}</a>.'.format(url, name)
        except IndexError:
            text = 'Please enter the correct format:\n/unsub url'
        except (TypeError, AttributeError):
            text = 'No such subscription.'
        finally:
            self.__send_html(chat_id, text)

    def rss(self, bot, update):
        chat_id = update.message.chat_id
        rss_list = self.database.get_rss_list_by_chat_id(chat_id)
        text = '<b>Your subscription:</b>\n'
        if len(rss_list) == 0:
            text = 'No subscription yet.'
        else:
            for rss in rss_list:
                text += '<a href="{}">{}</a>\n'.format(rss.url, rss.title)
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
