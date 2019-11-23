import time
__author__ = 'nvol'


class simpltmr:
    dct = {None: time.time()}

    @classmethod
    def init(cls, key=None):
        cls.dct[key] = time.time()

    @classmethod
    def has_run_out(cls, timeout=1.0, key=None):
        start_time = cls.dct.get(key)
        if not start_time or not timeout:
            return False # never run out
        return (time.time() - start_time) >= timeout

    @classmethod
    def exists(cls, key):
        return cls.dct.get(key)

    @classmethod
    def pop(cls, key):
        cls.dct.pop(key)