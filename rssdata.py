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
import json
import logging
import time

from util import absolute_path, default, singleton


@singleton
class Settings(object):

    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read(absolute_path('conf.ini'))

    @default("test")
    def get_noting(self):
        return self.config.get("default", "nothing")

    def get_token(self):
        return self.config.get("default", "token")

    @default(300)
    def get_interval(self):
        return int(self.config.get("default", "interval"))

    @default(3)
    def get_error_limit(self):
        return int(self.config.get("default", "errorlimit"))

    @default("lanthora")
    def get_admin(self):
        return self.config.get("default", "admin")

    @default(0)
    def get_sublimit(self):
        return int(self.config.get("default", "sublimit"))

    @default('<a href="https://github.com/lanthora/rssbot-beta/blob/master/README.md">README</a>')
    def get_start_msg(self):
        return self.config.get("default", "startmsg")

    @default(logging.ERROR)
    def get_log_level(self):
        if self.config.get("default", "loglevel") == "DEBUG":
            return logging.DEBUG
        elif self.config.get("default", "loglevel") == "INFO":
            return logging.INFO
        else:
            return logging.ERROR


@singleton
class DataFactory(object):
    def __init__(self):
        self.data: dict = {}
        self.__loaded: bool = False
        self.__dumped: bool = False
    def load(self):
        if self.__loaded:
            return
        self.__loaded = True
        self.data = self.__restore(absolute_path("database.json"))

    @default({})
    def __restore(self, path):
        logging.info("加载数据")
        with open(path, "r", encoding="UTF-8") as f:
            return json.load(f)

    def dump(self):
        if(self.__dumped):
            return
        self.__dumped = True

        logging.info("保存数据")
        with open(absolute_path("database.json"), "w", encoding="UTF-8") as f:
            json.dump(self.data, f, ensure_ascii=False)

    def get_error_times_db(self):
        self.load()
        return self.data.setdefault("et", {})

    def get_regular_exp_db(self):
        self.load()
        return self.data.setdefault("re", {})

    def get_recently_used_elements_db(self):
        self.load()
        return self.data.setdefault("rue", {})

    @default(False)
    def set_regular_exp_by_chatid_and_rss(self, chat_id, url, regular):
        user_re_db: dict = self.get_regular_exp_db().setdefault(str(chat_id), {})
        user_re_db[str(url)] = str(regular)
        return True

    @default(None)
    def get_regular_exp_by_chatid_and_rss(self, chat_id, url):
        return self.get_regular_exp_db()[str(chat_id)][str(url)]


@singleton
class RecentlyUsedElements():
    def __init__(self, dict_limit: int = 50):
        self.dict = DataFactory().get_recently_used_elements_db()
        self.dict_limit = dict_limit

    def has_element(self, element: str, url: str = None) -> bool:
        logging.debug("查重 {}".format(url))
        return self.__has_element_dict(url, element)

    def __has_element_dict(self, url: str, element: str):
        dict_url = self.dict.setdefault(str(url), {})
        current_time = time.time()
        save_time = dict_url.setdefault(str(element), current_time)
        self.__release_memory(dict_url)
        return current_time != save_time

    def __release_memory(self, dict_url: dict):
        if len(dict_url) < self.dict_limit:
            logging.debug("检查当前rss缓存数目 {}".format(len(dict_url)))
            return

        logging.debug("释放前缓存数目 {}".format(len(dict_url)))
        while len(dict_url) > self.dict_limit * 0.6:
            logging.debug("释放时缓存数目 {}".format(len(dict_url)))
            self.__randomly_delete_the_earliest_added_element(dict_url)

        logging.debug("释放后缓存数目 {}".format(len(dict_url)))

    def __randomly_delete_the_earliest_added_element(self, dict_url: dict):
        random_key = random.choice(list(dict_url.keys()))

        logging.debug("dict_url.get(random_key) {}".format(
            dict_url.get(random_key)))
        for _ in range(1, 3):
            new_random_key = random.choice(list(dict_url.keys()))
            if dict_url.get(new_random_key) < dict_url.get(random_key):
                random_key = new_random_key
            logging.debug("dict_url.get(random_key) {}".format(
                dict_url.get(random_key)))
        logging.debug("random_key {}".format(random_key))
        dict_url.pop(random_key)

    def remove_cache(self, url: str):
        try:
            self.dict.pop(url)
        except KeyError:
            pass
        finally:
            logging.info("清空缓存 {}".format(url))


if __name__ == "__main__":
    rue: RecentlyUsedElements = RecentlyUsedElements()
    print(rue.has_element(1, 2))
    print(rue.has_element(1, 2))
    print(rue.has_element(1, 2))
    DataFactory().dump()
