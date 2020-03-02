# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#                                                                             #
#     Copyright (C)     2019-2020   lanthora                                  #
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
import signal
import sys
import time
from concurrent.futures import ThreadPoolExecutor

from telegram import Bot
from telegram.error import BadRequest, Unauthorized
from telegram.ext import CommandHandler, Job, Updater

import util
from rssdatabase import RSSdatabase
from rssfetcher import ParseError, RSSFethcer
from util import RecentlyUsedElements


class RSSBot(object):
    def __init__(self):
        self.__config = configparser.ConfigParser()
        self.__config.read('conf.ini')

        self.bot = Bot(self.__config.get("default", "token"))
        self.updater = Updater(
            token=self.__config.get("default", "token"),
            use_context=True
        )
        self.dp = self.updater.dispatcher
        self.jq = self.updater.job_queue
        self.freq = int(self.__config.get("default", "freq"))

        self.fether = RSSFethcer()
        self.database = RSSdatabase()

        self.et = {}
        self.el = self.__config.get("default", "errorlimit")

        self.recently_used_elements = RecentlyUsedElements()

        self.executor = ThreadPoolExecutor()

        signal.signal(signal.SIGINT, self.__sig_handler)
        signal.signal(signal.SIGTERM, self.__sig_handler)

    def __send_html(self, chat_id, text):
        self.bot.send_message(
            chat_id, text,
            parse_mode='HTML',
            disable_web_page_preview=True
        )

    def __can_sub(self, chat_id, username):
        logging.info("检查 {} 是否有权限订阅".format(username))
        admin = self.__config.get("default", "admin")
        sublimit = int(self.__config.get("default", "sublimit"))
        current_sub = len(self.database.get_sub_by_chat_id(chat_id))
        if username == admin or current_sub < sublimit:
            logging.info("{} 可以进行订阅操作".format(username))
            return True
        else:
            logging.info("{} 禁止进行订阅操作".format(username))
            return False

    def __error(self, update, context):
        try:
            raise context.error
        except BaseException as e:
            logging.error(e)

    def __refresh(self, context):
        logging.info("开始刷新所有订阅")
        rss_list = self.database.get_rss_list()
        if len(rss_list) == 0:
            return
        delta = self.freq/len(rss_list)
        for rss in rss_list:
            self.executor.submit(self.__update, rss.url)
            time.sleep(delta)

    def __update(self, url):
        logging.info("开始更新 {}".format(url))
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
                    logging.info("所有新文章处理完毕 {}".format(rssitem.title))
                    break
                elif self.recently_used_elements.has_element(iid, url):
                    logging.info("此文章最近推送过 {}".format(rssitem.name))
                    continue
                else:
                    rssitems.append(rssitem)
                    logging.info("添加新文章 {}".format(rssitem.name))
            if not normal:
                rssitems.clear()
                logging.info("出现异常，清空所有文章 {}".format(rssitem.title))
            self.et[url] = 0
            if len(rssitems) > 0:
                logging.info("准备发送更新 {}".format(rssitem.title))
                self.__send(rssitems, chats)

        except (ParseError, IndexError):
            self.et[url] = self.et.setdefault(url, 0) + 1
            if self.et[url] >= int(self.el):
                self.database.set_active(url, False)
                title = self.database.get_rss_by_url(url).title
                text = '<a href="{}">{} </a>'.format(url, title)
                text += '更新时出现错误，已停止推送，请检查无误后重新订阅'
                for chat_id in chats:
                    self.__send_html(chat_id, text)

    def __send(self, rssitems, chats):
        _text = ''
        _url = rssitems[0].url
        while len(rssitems):
            rssitem = rssitems.pop()
            _text += '\n<a href="{}">{}</a>'.format(rssitem.link, rssitem.name)
            logging.info("取出文章标题添加到要发送到字符串 {}".format(rssitem.name))

        logging.info("需要发送的用户数 {}".format(len(chats)))
        for chat_id in chats:
            logging.info("查询的url {}".format(_url))
            logging.info("查询的chat_id {}".format(chat_id))
            nickname = self.database.get_nickname(_url, chat_id)
            logging.info("获取别名 {}".format(nickname))
            _title = '<b>{}</b>'.format(nickname)
            text = _title + _text
            logging.info("组合成最终需要发送的字符串 {}".format(text))
            try:
                self.__send_html(chat_id, text)
            except (BadRequest, Unauthorized):
                self.database.del_sub('', chat_id)
            except BaseException as base_exception:
                logging.error(base_exception)

    def start(self, update, context):
        chat_id = update.message.chat_id
        text = self.__config.get("default", "startmsg")
        self.__send_html(chat_id, text)

    def subscribe(self, update, context):
        chat_id = update.message.chat_id
        username = update.effective_user.username
        logging.info("{} 发起订阅".format(username))
        if not self.__can_sub(chat_id, username):
            sublimit = int(self.__config.get("default", "sublimit"))
            text = '订阅上限为 <i>{}</i> , 您已达到订阅上限\n'.format(sublimit)
            text += '请根据 /start 中的指引自行构建'
            self.__send_html(chat_id, text)
            logging.info("向 {} 反馈已经达到订阅上限".format(username))
            return
        try:
            url = update.message.text.split(' ')[1]
            logging.info("从命令中拆分出订阅url {}".format(url))
            rss = self.fether.check_url(url)
            logging.info("请求url并返回rss对象")
            if rss.active:
                self.database.add_rss(rss)
                self.database.add_sub(rss.url, chat_id)
                _text = '已订阅: <a href="{}">{}</a>'
                text = _text.format(rss.url, rss.title)
            else:
                issue = "https://github.com/lanthora/rssbot-beta/issues"
                text = '暂不支持此RSS，请<a href="{}">上报</a>'.format(issue)
        except IndexError:
            text = '请输入正确的格式:\n/sub url'
        finally:
            self.__send_html(chat_id, text)

    def unsubscribe(self, update, context):
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

    def rss(self, update, context):
        chat_id = update.message.chat_id
        sub_list = self.database.get_sub_by_chat_id(chat_id)
        text = '<b>你的订阅:</b>\n'
        active_rss = '▫️<a href="{}">{}</a>\n'
        inactive_rss = '▪️<a href="{}">{}</a>\n'
        if len(sub_list) == 0:
            text = '暂无订阅'
        else:
            for rss in sub_list:
                if bool(rss.active) == True:
                    text += active_rss.format(rss.url, rss.title)
                else:
                    text += inactive_rss.format(rss.url, rss.title)
        self.__send_html(chat_id, text)

    def rename(self, update, context):
        chat_id = update.message.chat_id
        try:
            url = update.message.text.split(' ')[1]
            nickname = ' '.join(update.message.text.split(' ')[2:]).strip()
            logging.info("更新的别名为 {}".format(nickname))
            self.database.set_nickname(url, chat_id, nickname)
            text = '别名已更新为: <a href="{}">{}</a>'.format(url, nickname)
        except IndexError:
            text = '请输入正确的格式:\n/rename url nickname'
        except BaseException as base_exception:
            logging.error(base_exception)
            issue = "https://github.com/lanthora/rssbot-beta/issues"
            text = '发生未知错误，请<a href="{}">上报</a>'.format(issue)
        finally:
            self.__send_html(chat_id, text)

    def run(self):
        self.dp.add_handler(CommandHandler('start', self.start))
        self.dp.add_handler(CommandHandler('sub', self.subscribe))
        self.dp.add_handler(CommandHandler('unsub', self.unsubscribe))
        self.dp.add_handler(CommandHandler('rss', self.rss))
        self.dp.add_handler(CommandHandler('rename', self.rename))
        self.dp.add_error_handler(self.__error)
        self.jq.run_repeating(self.__refresh, self.freq, first=5)
        self.jq.start()
        self.updater.start_polling()

    def __sig_handler(self, signal, frame):
        self.jq.stop()
        sys.exit(0)
