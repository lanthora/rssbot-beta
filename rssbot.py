# SPDX-License-Identifier: GPL-3.0-or-later
import logging
import threading
from concurrent.futures import ThreadPoolExecutor

from telegram import Bot
from telegram.error import BadRequest, Unauthorized
from telegram.ext import CommandHandler, Job, Updater

from rssdata import NoSQLDB, RecentlyUsedElements, RegularExpression, Settings
from rssdatabase import RSSdatabase
from rssfetcher import ParseError, RSSFethcer
from util import md5sum, regular_match


class RSSBot(object):
    def __init__(self):
        self.bot = Bot(Settings().get_token())
        self.updater = Updater(token=Settings().get_token(), use_context=True)
        self.dp = self.updater.dispatcher
        self.interval = Settings().get_interval()
        self.fether = RSSFethcer()
        self.database = RSSdatabase()
        self.et = NoSQLDB().get_error_times_db()
        self.el = Settings().get_error_limit()
        self.recently_used_elements = RecentlyUsedElements()
        self.executor = ThreadPoolExecutor(max_workers=64)
        self.running = True
        self.semaphore = threading.Semaphore(0)
        self.re_db = RegularExpression()

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
                self.running = False
                break

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
                    break

                # 出现三篇最近推送过的文章,即使mark不匹配，也是视为正常匹配
                # 这个策略可以用来解决最近文章被替换的问题
                elif self.recently_used_elements.has_element(iid, url):
                    continue_times += 1
                    if continue_times < 3:
                        continue
                    else:
                        normal = (len(rssitems) != 0)
                        break
                else:
                    rssitems.append(rssitem)

            if not normal:
                rssitems.clear()
                logging.info("更新异常 清理推送 {}".format(url))
            self.et[url] = 0

            if len(rssitems) > 0:
                self.__send(rssitems, chats)

        except (ParseError, IndexError):
            self.et[url] = self.et.setdefault(url, 0) + 1
            if self.et[url] >= int(self.el):
                self.database.set_active(url, False)
                title = self.database.get_rss_by_url(url).title
                text = '<a href="{}">{} </a>'.format(url, title)
                text += '更新时出现错误，已停止推送，请检查无误后重新订阅'
                logging.info("连续错误 停止推送{}".format(url))
                for chat_id in chats:
                    self.__send_html(chat_id, text)

    def __send(self, rssitems, chats):
        _text = ''
        _url = rssitems[0].url
        while len(rssitems):
            rssitem = rssitems.pop()
            _text += '\n<a href="{}">{}</a>'.format(rssitem.link, rssitem.name)

        for chat_id in chats:
            _text = regular_match(_text, self.re_db.get_re(chat_id, _url))
            if(_text == "\n"):
                continue

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

    def add_re(self, update, context):
        chat_id = update.message.chat_id
        try:
            _url = update.message.text.split(' ')[1]
            regular = ' '.join(update.message.text.split(' ')[2:]).strip()
            self.re_db.set_re(chat_id, _url, regular)
            text = '成功添加正则表达式 <a href="{}">{}</a>'.format(_url, regular)
            re_add_log = "添加正则表达式 {} , {} -> {}"
            logging.info(re_add_log.format(chat_id, _url, regular))
        except IndexError:
            text = '请输入正确的格式:\n/addre url regular'
        except:
            text = '发生未知错误'
        finally:
            self.__send_html(chat_id, text)

    def del_re(self, update, context):
        chat_id = update.message.chat_id
        try:
            _url = update.message.text.split(' ')[1]
            rm_re_view = '成功移除正则表达式 <a href="{}">{}</a>'
            text = rm_re_view.format(_url, self.re_db.get_re(chat_id, _url))
            self.re_db.rm_re(chat_id, _url)
            re_rm_log = "移除正则表达式 {} , {}"
            logging.info(re_rm_log.format(chat_id, _url))
        except IndexError:
            text = '请输入正确的格式:\n/delre url'
        except:
            text = '发生未知错误'
        finally:
            self.__send_html(chat_id, text)

    def run(self):
        self.dp.add_handler(CommandHandler('start', self.start))
        self.dp.add_handler(CommandHandler('sub', self.subscribe))
        self.dp.add_handler(CommandHandler('unsub', self.unsubscribe))
        self.dp.add_handler(CommandHandler('rss', self.rss))
        self.dp.add_handler(CommandHandler('rename', self.rename))
        self.dp.add_handler(CommandHandler('addre', self.add_re))
        self.dp.add_handler(CommandHandler('delre', self.del_re))
        self.dp.add_error_handler(self.__error)
        self.updater.start_polling()

        while self.running:
            self.__refresh()

        NoSQLDB().dump()
        self.updater.stop()

    def stop(self):
        self.semaphore.release()
