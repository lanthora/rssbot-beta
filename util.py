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
import hashlib
import json
import logging
import random
import sys
import time


def md5sum(plain: str) -> str:
    hl = hashlib.md5()
    hl.update(str(plain).encode(encoding='utf-8'))
    crypt = hl.hexdigest()
    return crypt


def absolute_path(relative_path: str) -> str:
    return "{}/{}".format(sys.path[0], relative_path)


class RecentlyUsedElements():
    def __init__(self, dict_limit: int = 50):

        self.dict = {}
        self.dict_limit = dict_limit
        self.__load()

    def has_element(self, element: str, url: str = None) -> bool:
        logging.debug("查重 {}".format(url))
        return self.__has_element_dict(url, element)

    def __has_element_dict(self, url: str, element: str):
        if self.dict.get(url) == None:
            logging.debug("添加新的rss {}".format(url))
            self.dict[url] = {}

        dict_url = self.dict[url]
        ret = dict_url.get(element)

        if ret == None:
            dict_url[element] = time.time()
            logging.debug("添加新的article {}".format(element))

        self.__release_memory(dict_url)

        return ret != None

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

    def __load(self):
        try:
            with open(absolute_path("dict.json"), "r", encoding="UTF-8") as f:
                self.dict = json.load(f)
                logging.info("程序启动 读取缓存文件 dict.json")
        except FileNotFoundError:
            logging.debug("缓存文件不存在 dict.json")
        except json.decoder.JSONDecodeError:
            logging.debug("缓存文件内容为空 dict.json")

    def dump(self):
        logging.info("中断信号 保存dict.json")
        with open(absolute_path("dict.json"), "w", encoding="UTF-8") as f:
            json.dump(self.dict, f, ensure_ascii=False)

    def remove_cache(self, url: str):
        try:
            self.dict.pop(url)
        except KeyError:
            # 被移除的url根本没有缓存
            pass
        finally:
            logging.info("清空缓存 {}".format(url))


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        format="%(asctime)s - %(message)s")
    rue = RecentlyUsedElements(5)
    print(rue.has_element("1", "123"))  # False
    print(rue.has_element("1", "123"))  # False
    print(rue.has_element("1", "123"))  # False
    print(rue.has_element("1", "123"))  # False
    print(rue.has_element("1", "123"))  # False

    time.sleep(60)
