from .Global import *
from threading import Thread


class SystemThreads:
    def __init__(self):
        self.sys_threads = dict()

    def __repr__(self):
        ret = ''
        for i in self.sys_threads:
            ret += '\t\t' + str(i) + ': ' + str(self.sys_threads[i]) + '\n'
        return ret

    def __iter__(self):
        return self.sys_threads.__iter__()

    def not_exists_or_dead(self, name):
        return name not in self.sys_threads or \
          not self.sys_threads[name].is_alive()

    def start_thread(self, func, name=None, f_args=None):
        name = name or func.__name__
        #print('name:', name)
        #print('threads:', str(self.sys_threads))
        if self.not_exists_or_dead(name):
            log.info(paint('\n\n +++ creating thread %s\n' % str(name), GREEN))
            if f_args:
                self.sys_threads[name] = Thread(target=func, name=name, args=f_args)
            else:
                self.sys_threads[name] = Thread(target=func, name=name)
            self.sys_threads[name].start()
        else:
            log.warning('\n\n --- thread %s is already running!\n' % str(name))

    def join(self, name):
        th = self.sys_threads.get(name)
        if th:
            th.join()
