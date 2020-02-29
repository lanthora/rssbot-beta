import hashlib
import logging
import random
import time


def md5sum(plain: str) -> str:
    hl = hashlib.md5()
    hl.update(str(plain).encode(encoding='utf-8'))
    crypt = hl.hexdigest()
    return crypt


class RecentlyUsedElements():
    def __init__(self, dict_limit: int = 50):

        self.dict = {}
        self.dict_limit = dict_limit

    def has_element(self, element: str, url: str = None) -> bool:
        logging.info("查重 {}".format(url))
        return self.__has_element_dict(url, element)

    def __has_element_dict(self, url: str, element: str):
        if self.dict.get(url) == None:
            logging.info("添加新的rss {}".format(url))
            self.dict[url] = {}

        dict_url = self.dict[url]
        ret = dict_url.get(element)

        if ret == None:
            dict_url[element] = time.time()
            logging.info("添加新的article {}".format(element))

        self.__release_memory(dict_url)

        return ret != None

    def __release_memory(self, dict_url: dict):
        if len(dict_url) < self.dict_limit:
            logging.info("检查当前rss缓存数目 {}".format(len(dict_url)))
            return

        logging.info("释放前缓存数目 {}".format(len(dict_url)))
        while len(dict_url) > self.dict_limit * 0.6:
            logging.info("释放时缓存数目 {}".format(len(dict_url)))
            self.__randomly_delete_the_earliest_added_element(dict_url)
            
        logging.info("释放后缓存数目 {}".format(len(dict_url)))

    def __randomly_delete_the_earliest_added_element(self, dict_url: dict):
        random_key = random.choice(list(dict_url.keys()))
        
        logging.info("dict_url.get(random_key) {}".format(dict_url.get(random_key)))
        for _ in range(1, 3):
            new_random_key = random.choice(list(dict_url.keys()))
            if dict_url.get(new_random_key) < dict_url.get(random_key):
                random_key = new_random_key
            logging.info("dict_url.get(random_key) {}".format(dict_url.get(random_key)))
        logging.info("random_key {}".format(random_key))
        dict_url.pop(random_key)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    rue = RecentlyUsedElements(5)
    print(rue.has_element("1", "123"))  # False
    print(rue.has_element("2", "123"))  # False
    print(rue.has_element("3", "123"))  # False
    print(rue.has_element("4", "123"))  # False
    print(rue.has_element("5", "123"))  # False
    print(rue.has_element("6", "123"))  # False
    print(rue.has_element("7", "123"))  # False
