import signal

# Common imports for all modules importing Global
from .logger_init import *
from time import sleep

log = ColoredLogger().root_logger

#### CLASS GLOBAL ####
# must be imported in every module
class Global:
    run = True

    def __init__(self):
        pass

    @classmethod
    def signal_handler(cls, arg1, arg2):
        print('{!signal handler called!}')
        cls.run = False

# bind SIGINT to quit handler (need to stop loops by Ctrl+C)
signal.signal(signal.SIGINT, Global.signal_handler)

# __all__ = dir()
# for key in __all__:
#     if '__' in key:
#         __all__.remove(key)
# __all__.remove('signal')
