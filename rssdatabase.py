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
import sqlite3

from rssmodule import RSS


class RSSdatabase(object):
    def __init__(self):
        self.__config = configparser.ConfigParser()
        self.__config.read('conf.ini')
        self.dbname = self.__config.get("default", "dbname")
        self.sqlfile = self.__config.get("default", "sqlfile")

        if self.__need_create_table():
            conn, cursor = self.__open()
            with open(self.sqlfile, 'r') as f:
                sql = f.read()
                cursor.executescript(sql)
                conn.commit()
            self.__close(cursor, conn)

    def __need_create_table(self):
        conn, cursor = self.__open()
        try:
            sql = 'select count(*)  from sqlite_master where type="table" and (name = "RSS" or name = "SUB")'
            cursors = cursor.execute(sql)
            ret = cursors.fetchone()[0]
        finally:
            self.__close(cursor, conn)
            return ret != 2

    def __open(self):
        """ conn, cursor = self.__open() """
        conn = sqlite3.connect(self.dbname)
        cursor = conn.cursor()
        return conn, cursor

    def __close(self, cursor, conn):
        """ self.__close(cursor, conn) """
        cursor.close()
        conn.close()

    def add_rss(self, rss=RSS()):
        conn, cursor = self.__open()
        try:
            sql = 'SELECT count(*) FROM RSS WHERE URL=? LIMIT 1'
            cursors = cursor.execute(sql, (rss.url,))
            ret = cursors.fetchone()[0]
            if ret != 0:
                return
            sql = "INSERT INTO RSS(URL,TITLE,MARK) VALUES(?,?,?)"
            cursors = cursor.execute(sql, (rss.url, rss.title, rss.mark))
            conn.commit()
        finally:
            self.__close(cursor, conn)

    def add_sub(self, url='', chat_id=''):
        conn, cursor = self.__open()
        try:
            sql = 'SELECT count(*) FROM SUB WHERE URL=? AND CHAT_ID=? LIMIT 1'
            cursors = cursor.execute(sql, (url, chat_id))
            ret = cursors.fetchone()[0]
            if ret != 0:
                return
            sql = "INSERT INTO SUB(URL,CHAT_ID) VALUES(?,?)"
            cursors = cursor.execute(sql, (url, chat_id))
            conn.commit()
        finally:
            self.__close(cursor, conn)

    def del_sub(self, url='', chat_id=''):
        conn, cursor = self.__open()
        try:
            if url == '':
                sql = "DELETE FROM SUB WHERE CHAT_ID=?"
                cursor.execute(sql, (chat_id,))
            else:
                sql = "DELETE FROM SUB WHERE URL=? AND CHAT_ID=?"
                cursor.execute(sql, (url, chat_id))
            conn.commit()
        finally:
            self.__close(cursor, conn)

    def set_mark(self, url='', mark=''):
        conn, cursor = self.__open()
        try:
            sql = 'UPDATE RSS SET MARK=? WHERE URL=?'
            cursor.execute(sql, (mark, url))
            conn.commit()
        finally:
            self.__close(cursor, conn)

    def set_active(self, url='', status=False):
        conn, cursor = self.__open()
        try:
            sql = 'UPDATE RSS SET ACTIVE=? WHERE URL=?'
            cursor.execute(sql, (status, url))
            conn.commit()
        finally:
            self.__close(cursor, conn)

    def get_mark(self, url=''):
        conn, cursor = self.__open()
        try:
            mark = None
            sql = 'SELECT MARK FROM RSS WHERE URL=?'
            cursors = cursor.execute(sql, (url,))
            mark = cursors.fetchone()[0]
        finally:
            self.__close(cursor, conn)
            return mark

    def get_chats_by_url(self, url=''):
        conn, cursor = self.__open()
        try:
            chats = []
            sql = 'SELECT CHAT_ID FROM SUB WHERE URL=?'
            cursors = cursor.execute(sql, (url,))
            for chat_id in cursors:
                chats.append(chat_id[0])
        finally:
            self.__close(cursor, conn)
            return chats

    def get_rss_by_url(self, url=''):
        conn, cursor = self.__open()
        try:
            rss = None
            sql = 'SELECT * FROM RSS WHERE URL=?'
            cursors = cursor.execute(sql, (url,))
            _ = cursors.fetchone()
            rss = RSS(_[1], _[0], _[2], _[3])
        finally:
            self.__close(cursor, conn)
            return rss

    def get_rss_list_by_chat_id(self, chat_id=''):
        conn, cursor = self.__open()
        try:
            rss_list = []
            if chat_id != '':
                sql = 'SELECT * FROM RSS WHERE URL IN (SELECT URL FROM SUB WHERE CHAT_ID=?)'
                cursors = cursor.execute(sql, (chat_id,))
            else:
                sql = 'SELECT * FROM RSS WHERE ACTIVE=1 AND URL IN (SELECT URL FROM SUB)'
                cursors = cursor.execute(sql)
            for _ in cursors:
                url = _[0]
                title = _[1]
                mark = _[2]
                active = _[3]
                rss_list.append(RSS(title, url, mark, active))
        finally:
            self.__close(cursor, conn)
            return rss_list
