import hashlib


def md5sum(plain):
    hl = hashlib.md5()
    hl.update(str(plain).encode(encoding='utf-8'))
    crypt = hl.hexdigest()
    return crypt
