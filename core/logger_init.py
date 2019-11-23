from logging import *
import logging.handlers
import os
import time

MNT_PATH = '/mnt/lbx/'
LOG_PATH = MNT_PATH + 'logs'

logging_save = False
try:
    from logging_level import *
except:
    logging_level = logging.INFO # choose: DEBUG, INFO, WARNING

RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[0;33m'
BLUE = '\033[0;34m'
MAGENTA = '\033[0;35m'
CYAN = '\033[0;36m'
GRAY = '\033[0;37m'
GREY = GRAY
NORMAL = '\033[0m'
RED_INV = '\033[7;31m'
GREEN_INV = '\033[7;32m'
YELLOW_INV = '\033[7;33m'
BLUE_INV = '\033[7;34m'
MAGENTA_INV = '\033[7;35m'
CYAN_INV = '\033[7;36m'
GRAY_INV = '\033[7;37m'
GREY_INV = GRAY_INV

def paint(message, color):
    return color + str(message) + NORMAL

class ColoredLogging(Logger):
    def __init__(self, name, level=NOTSET):
        super().__init__(name, level)
    def debug(self, msg, *args, **kwargs):
        if self.isEnabledFor(DEBUG):
            self._log(DEBUG, paint(msg, MAGENTA), args, **kwargs)
    def warning(self, msg, *args, **kwargs):
        if self.isEnabledFor(WARNING):
            self._log(WARNING, paint(msg, YELLOW), args, **kwargs)
    def error(self, msg, *args, **kwargs):
        if self.isEnabledFor(ERROR):
            self._log(ERROR, paint(msg, RED), args, **kwargs)
    def critical(self, msg, *args, **kwargs):
        if self.isEnabledFor(CRITICAL):
            self._log(CRITICAL, paint(msg, RED_INV), args, **kwargs)


class ColoredLogger:
    def __init__(self):
        print('INITIALIZING COLORED LOGGER')
        if not os.path.isdir(LOG_PATH) and logging_save:
            os.mkdir(LOG_PATH)

        f = logging.Formatter(
          fmt='[%(levelname)s:%(asctime)s.%(msecs)d '
            '%(filename)s->%(funcName)s{%(lineno)d}] '
            '%(message)s',
          datefmt='%Y%m%d_%H%M%S'
        )

        log_time = time.strftime("%Y%m%d_%H%M%S",
                time.localtime(time.time()))

        handlers = [logging.StreamHandler()]
        if logging_save:
            handlers.append(
              logging.handlers.RotatingFileHandler(
                LOG_PATH + '/Core_{0}.log'.format(log_time),
                encoding='utf8',
                maxBytes=4194304,
                backupCount=9
              )
            )
        #handlers = [
        #  logging.handlers.RotatingFileHandler(
        #    LOG_PATH + '/Core_{0}.log'.format(log_time),
        #    encoding='utf8',
        #    maxBytes=4194304,
        #    backupCount=9
        #  ),
        #  logging.StreamHandler()
        #]

        self.root_logger = ColoredLogging('colored')
        self.root_logger.setLevel(logging_level)

        for h in handlers:
            h.setFormatter(f)
            h.setLevel(logging_level)
            self.root_logger.addHandler(h)
