# SPDX-License-Identifier: GPL-3.0-or-later
import logging
import threading
from concurrent.futures import ThreadPoolExecutor

from telegram import Bot
from telegram.error import BadRequest, Unauthorized
from telegram.ext import CommandHandler, Job, Updater

from rssdata import Settings
from rssdatabase import RSSdatabase
from rssfetcher import ParseError, RSSFethcer
from util import md5sum


class RSSBot(object):
    def __init__(self):
        self.bot = Bot(Settings().get_token())
        self.updater = Updater(token=Settings().get_token(), use_context=True)
        self.dp = self.updater.dispatcher
        self.interval = Settings().get_interval()
        self.fether = RSSFethcer()
        self.database = RSSdatabase()
        self.executor = ThreadPoolExecutor(max_workers=50)
        self.running = True
        self.semaphore = threading.Semaphore(0)
        self.errcnt = {}

    def __send_html(self, chat_id, text):
        self.bot.send_message(
            chat_id, text,
            parse_mode='HTML',
            disable_web_page_preview=True
        )

    def __can_sub(self, chat_id, username):
        admin = Settings().get_admin()
        sublimit = Settings().get_sublimit()
        current_sub = len(self.database.get_sub_by_chat_id(chat_id))
        return (username == admin or current_sub < sublimit)

    def __error(self, update, context):
        try:
            raise context.error
        except BaseException as e:
            logging.error(e)

    def __refresh(self):
        rss_list = self.database.get_rss_list()
        if len(rss_list) == 0:
            return
        delta = self.interval/len(rss_list)
        for rss in rss_list:
            self.executor.submit(self.__update, rss.url)
            if self.semaphore.acquire(timeout=delta):
                break

    def __update_error_handler(self, url, chats, retry):
        cnt = self.errcnt.get(url, 0)
        if retry and cnt < 24 * 60 / self.interval:
            logging.info("更新出错 {}".format(url))
            self.errcnt[url] = cnt + 1
            return

        self.database.set_active(url, False)
        title = self.database.get_rss_by_url(url).title
        text = '<a href="{}">{} </a>'.format(url, title)
        text += '更新时出现错误，已停止推送，请检查无误后重新订阅'
        logging.info("停止推送 {}".format(url))
        for chat_id in chats:
            self.__send_html(chat_id, text)

    def __update(self, url):
        try:
            chats = self.database.get_chats_by_url(url)
            mark = self.database.get_mark(url)
            _rssitems = self.fether.update_rss(url)
            self.database.set_mark(url, _rssitems[0].mark)
            rssitems = []
            normal = False
            continue_times = 0
            for rssitem in _rssitems:
                iid = md5sum(rssitem.mark)
                if rssitem.mark == mark:
                    normal = True
                    self.errcnt[url] = 0
                    break

                rssitems.append(rssitem)

            if not normal:
                rssitems.clear()
                self.__update_error_handler(url, chats, True)

            if len(rssitems) > 0:
                self.__send(rssitems, chats)

        except (ParseError, IndexError):
            self.__update_error_handler(url, chats, True)


    def __send(self, rssitems, chats):
        _text = ''
        _url = rssitems[0].url
        while len(rssitems):
            rssitem = rssitems.pop()
            _text += '\n<a href="{}">{}</a>'.format(rssitem.link, rssitem.name)

        for chat_id in chats:
            nickname = self.database.get_nickname(_url, chat_id)

            _title = '<b>{}</b>'.format(nickname)
            text = _title + _text

            try:
                self.__send_html(chat_id, text)
            except (BadRequest, Unauthorized):
                self.database.del_sub('', chat_id)
            except BaseException as base_exception:
                logging.error(base_exception)

    def start(self, update, context):
        chat_id = update.message.chat_id
        text = Settings().get_start_msg()
        self.__send_html(chat_id, text)

    def subscribe(self, update, context):
        chat_id = update.message.chat_id
        username = update.effective_user.username

        if not self.__can_sub(chat_id, username):
            sublimit = Settings().get_sublimit()
            text = '订阅上限为 <i>{}</i> , 您已达到订阅上限\n'.format(sublimit)
            text += '请根据 /start 中的指引自行构建'
            self.__send_html(chat_id, text)
            logging.info("达到上限 {}".format(chat_id))
            return
        try:
            url = update.message.text.split(' ')[1]
            rss = self.fether.check_url(url)
            if rss.active:
                self.database.add_rss(rss)
                self.database.add_sub(rss.url, chat_id)
                _text = '已订阅: <a href="{}">{}</a>'
                text = _text.format(rss.url, rss.title)
                logging.info("成功订阅 {} -> {}".format(chat_id, url))
            else:
                issue = "https://github.com/lanthora/rssbot-beta/issues"
                text = '暂不支持此RSS, 请<a href="{}">上报</a>'.format(issue)
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
            logging.info("取消订阅 {} -> {}".format(chat_id, url))
            if(self.database.get_sub_num_by_url(url) == 0):
                self.recently_used_elements.remove_cache(url)

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
        self.updater.start_polling()

        while self.running:
            self.__refresh()

        self.updater.stop()

    def stop(self):
        self.running = False
        self.semaphore.release()
