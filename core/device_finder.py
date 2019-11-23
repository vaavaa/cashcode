from .Global import *
from glob import glob
from .core import Core
from core.sthreads import SystemThreads

class DeviceFinder:
    @classmethod
    def _get_all_ports(cls):
        return set(glob('/dev/tty[UA][SC][BM]*'))

    @classmethod
    def _get_occupied_ports(cls):
        serial_modules = {Core.modules[k] for k in Core.modules \
          if Core.modules[k].protocol == 'serial'}
        return {module.port for module in serial_modules if module.port is not None}

    @classmethod
    def get_free_ports(cls):
        return cls._get_all_ports() - cls._get_occupied_ports()

    # @classmethod
    # def _occupy_port(cls, module_name, port):
    #     if cls.ports.get(module_name) is None:
    #         cls.ports[module_name] = port
    #         return True
    #     return False

    # @classmethod
    # def _release_port(cls, port_or_module_name):
    #     if port_or_module_name in cls.ports:
    #         if cls.ports.get(port_or_module_name) is not None:
    #             cls.ports[port_or_module_name] = None
    #             return True
    #     elif port_or_module_name in cls.ports.values():
    #         keys = [i[0] for i in cls.ports.items() if i[1] == port_or_module_name]
    #         if len(keys) >= 1: #@@@ must be == 1!!! FIXME
    #             for k in keys:
    #                 cls.ports[k] = None
    #             return True
    #     return False

    @classmethod
    def launch_device_finder(cls):
        cls._sth = SystemThreads()
        cls._sth.start_thread(cls.find_devices, 'serial-device-finder')

    @classmethod
    def find_devices(cls):
        # wait until core is done with launching modules
        Core.wait_for_ready_status()
        # check if there are any modules (with serial protocol) which
        # have no port
        module_ix = 0
        port_ix = 0
        while Global.run:
            free_ports = cls.get_free_ports()
            serial_modules = {Core.modules[k] for k in Core.modules \
              if Core.modules[k].protocol == 'serial'}
            modules_without_port = \
              {module for module in serial_modules if module.port is None}
            num_of_modules = len(modules_without_port)
            if module_ix >= num_of_modules:
                module_ix = 0
                port_ix = 0
            if modules_without_port:
                if free_ports:
                    # find port for one (the first in the list) module
                    if port_ix >= len(free_ports):
                        port_ix = 0
                    curr_module = list(modules_without_port)[module_ix]
                    curr_port = list(free_ports)[port_ix]
                    log.info('Implement find_device on %s with port %s' % \
                      (str(curr_module.name), str(curr_port)))
                    # list(modules_without_port)[module_ix].find_device(
                    #   list(free_ports)[port_ix], free_ports=list(free_ports))
                    curr_module.find_device(curr_port, free_ports=list(free_ports))
                    #---
                    port_ix += 1
                    if port_ix >= len(free_ports):
                        port_ix = 0
                        module_ix += 1
                        num_of_modules = len(modules_without_port)
                        if module_ix >= num_of_modules:
                            module_ix = 0
            else:
                break #@@@
            sleep(0.246)

