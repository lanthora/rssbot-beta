import hashlib


def md5sum(plain):
    hl = hashlib.md5()
    hl.update(str(plain).encode(encoding='utf-8'))
    crypt = hl.hexdigest()
    return crypt

class RecentlyUsedElements():
    def __init__(self, limit=1024):
        self.limit = limit
        self.current = 0
        self.data = [None]*limit

    def has_element(self, element):
        if element in self.data:
            return True
        else:
            self.current += 1
            self.data[(self.current) % self.limit] = element
            return False