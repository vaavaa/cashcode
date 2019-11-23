from .Global import *
import os


class Core:
    modules = dict()
    _status = None

    def __init__(self, modules_dict=None):
        self.__class__.modules = modules_dict
        if self.__class__.modules:
            self.__class__._launch_modules()
            self.__class__._status = 'ready'
        else:
            log.critical('No modules to run by core!')

    @classmethod
    def _launch_modules(cls):
        log.info('Modules to launch: %s' % str(cls.modules))
        for i in cls.modules:
            if hasattr(cls.modules[i], 'launch'):
                log.info('CORE is launching module %s...' % i)
                cls.modules[i].launch()
            else:
                log.info('CORE cannot find method "launch" for module %s' % cls.modules[i])
        print('all modules launched')

    @classmethod
    def get_status(cls):
        return cls._status

    # wait for core status 'ready'
    @classmethod
    def wait_for_ready_status(cls):
        while Global.run and cls._status != 'ready':
            sleep(0.05)

    @classmethod
    def quit(cls):
        Global.run = False
        tries = 78 # ~ *0.1 s
        log.info('CORE quitting: waiting for threads to terminate...')
        not_finished = True
        while not_finished:
            for module in cls.modules:
                threads = cls.modules[module]._threads
                not_finished = False in [threads.not_exists_or_dead(i) for i in threads.sys_threads]
                if not_finished:
                    break
            tries -= 1
            if not tries:
                break
            sleep(0.1)

        if not tries:
            threads_left = list()
            for module in cls.modules:
                threads = cls.modules[module]._threads
                threads_left += [i for i in threads.sys_threads \
                  if not threads.not_exists_or_dead(i)]
            log.error('system hangs on %s' % str(threads_left))
            log.error('emergency fallout!')
            os._exit(1) # it's not blessed! but we cannot cope with that now...
        else:
            log.info('        bye!')

