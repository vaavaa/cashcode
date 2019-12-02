from .Global import *
from .sthreads import SystemThreads
from .utils import are_lists_equal, to_tuple
from copy import deepcopy
from threading import Lock
from core.sender import Sender

DEFAULT_CHECK_CONNECTION_PERIOD = 2.5

class Module(object):
    #@@@ _devices_in_use = [] # TODO: to avoid checking devices that are already in use.

    def __init__(self):
        #@@@ self._interrupt = False

        # abstract
        self._protocol = None # 'serial', 'socket', ...
        self._port = None # for serial devices
        self._connection_settings = dict()
        self._ip_and_port = None # for socket devices
        self._name_and_id = None # class name and id(self) ("Scanner-1402374839")

        # base
        self._conn = None
        self._conn_lock = Lock()
        self._status = None
        self._request = None
        self._warnings = set() # non-critical errors
        self._alarms = set() # some essential events (one can use warnings instead)
        self._event_type = 'one dict' # 'one dict', 'separate dicts': events append behaviour
        self._events = list()
        self._threads = SystemThreads()

    @property
    def protocol(self):
        return self._protocol

    @property
    def port(self):
        return self._port

    @property
    def name(self):
        suffix = str(self._ip_and_port) if self._protocol == 'socket' else ''
        name_ = self._name_and_id
        if not name_:
            name_ = '-'.join([self.__class__.__name__, str(id(self))])
        if suffix:
            name_ += '-%s' % suffix
        return name_

    def launch(self):
        '''
        launch run() function in thread,
        usually this is made by Core
        '''
        # start thread if it is not running
        th_name = self.name
        if hasattr(self, 'run'):
            self._threads.start_thread(self.run, th_name)

        self.start_connection_checker()

    def start_connection_checker(self):
        '''
        start _connection_checker() function in thread if check_connection() exists
        '''
        if hasattr(self, 'check_connection'): # must be defined in child
            if self._status is None:
                self.update_status('no_connection')
            th_name = self.name + '-connection-checker'
            # start thread if it is not running
            self._threads.start_thread(self._connection_checker, th_name)

    def get_status(self):
        '''
        returns current module status and resets it if it ends with 'ed'
        '''
        ret = self._status
        if ret and ret.split()[0].endswith('ed'):
            self.update_status('unknown')
        return ret

    def update_status(self, new_status):
        if self._status != new_status:
            self._status = new_status
            log.info('\nstatus updated till [%s] for {%s}\n' %
              (paint(new_status, GREEN_INV), str(self.name)))

    def get_warnings(self):
        '''
        returns a set of warnings
        '''
        return self._warnings

    def update_warnings(self, action, wrnng):
        '''
        action is the one of the following: 'add', 'discard'
        '''
        new_set = self._warnings.copy()
        if action == 'add':
            new_set.add(wrnng)
        elif action == 'discard':
            new_set.discard(wrnng)
        if new_set != self._warnings:
            self._warnings = new_set
            log.info('\nwarnings updated till: %s for %s\n' %
              (paint(str(new_set), GREEN_INV), str(self.name)))

    def get_alarms(self):
        '''
        returns a set of alarms
        '''
        return self._alarms

    def update_alarms(self, action, alarm):
        '''
        action is the one of the following: 'add', 'discard'
        '''
        new_set = self._alarms.copy()
        if action == 'add':
            new_set.add(alarm)
        elif action == 'discard':
            new_set.discard(alarm)
        if new_set != self._alarms:
            self._alarms = new_set
            log.info('\nalarms updated till: %s for %s\n' %
              (paint(str(new_set), GREEN_INV), str(self.name)))

    def append_event(self, event_dict):
        prev_events = deepcopy(self._events)
        if 'one' in self._event_type:
            if self._events and len(self._events) > 0:
                for k in event_dict:
                    if k in self._events[0]:
                        if type(self._events[0][k]) in (int, float):
                            self._events[0][k] += event_dict[k]
                        elif type(self._events[0][k]) is list:
                            try:
                                self._events[0][k] += event_dict[k]
                            except:
                                self._events[0][k] += [event_dict[k]]
                        else:
                            self._events[0][k] = event_dict[k]
                    else:
                        self._events[0][k] = event_dict[k]
            else:
                self._events = [event_dict]
        else:
            if self._events and type(self._events) is list:
                self._events.append(event_dict)
            else:
                self._events = [event_dict]
        # check changes
        if not are_lists_equal(self._events, prev_events):
            log.info('\nnew events appeared for %s:\n%s\n' %
              (str(self.name), paint(self._events, GREEN_INV)))

    def get_events(self):
        if self._events is None:
            self._events = list()
        if self._events and len(self._events) > 0 and self._events[0]:
            log.info('\nevents flushed for %s:\n%s\n' %
              (str(self.name), paint(self._events, GREEN_INV)))
        ret = deepcopy(self._events)
        # flush
        self._events = list()
        if 'one' in self._event_type:
            if len(ret) > 0:
                return ret[0]
            else:
                return dict()
        return ret

    # def run(self):
    #     self.set_status('idle')
    #     # run connection checker
    #     ###@@@!!!@@@### self.sth.start_thread(self.connection_checker, 'Connection checker %s %s' %\
    #     ###@@@!!!@@@###     (str(self.protocol), str(self.id)))
    #     ###@@@!!!@@@### log.info(paint('Run loop started for %s.' % self.id, GREEN))
    #     while Global.run:
    #         # Get request
    #         req = self.get_request()
    #         sts = self.check_status()

    #         # Has request, and status is idle
    #         if req:
    #             self.request_handler(req)

    #             #only drop request if status has idle or 'ed' status
    #             sts = self.check_status()
    #             if sts == 'idle' or \
    #               sts.split()[0].endswith('ed'):
    #                 self.set_request(None)

    #         # Reset interrupt
    #         self._interrupt = False
    #         sleep(0.1)
    #     self.kill() # For putting devices to spleep before program closes
    #     log.info(paint('Run stopped exited for %s.' % self.id, GREEN))

    #--------------------------------------

    # def wait_for_status(self, status, timeout=5):
    #     # wait for idle state
    #     prev_sts = None
    #     tries = int(timeout/0.111)
    #     while Global.run and not self._interrupt:
    #         sts = self.get_status()
    #         if sts.split()[0] == status:
    #             return sts
    #         if sts != prev_sts:
    #             log.info('%s: status:::::::::::::::::::::::::::::::: %s' % \
    #                      (self.id, str(sts))) # @@@TODO@@@
    #             prev_sts = sts
    #         tries -= 1
    #         if not tries:
    #             break
    #         sleep(0.111)
    #     return False

    # # Interrupt all loops except for module run loop.
    # def send_interrupt(self):
    #     self._interrupt = True
    #     log.info('\n%s: Interrupt signal sent.\n' % self.id)

    ############################################
    ############ ABSTRACT FUNCTIONS ############
    #############  OVERRIDE THEM  ##############
    ############################################

    # # abstract (default)
    # def check_connection(self, just_after_reconnection=False):
    #     '''
    #     modifies status if needed (can update till 'no_connection')
    #     '''

    def _connection_checker(self):
        while Global.run:
            # check connection periodically
            if (self._protocol == 'serial' and self._port) or \
              (self._protocol == 'socket' and self._ip_and_port):
                if not self._conn:
                    # print('_conn_checker: trying to get connection')
                    connected = self._get_connection()
                    # print('connected:)' if connected else 'not connected :(', self._conn)
                    # print('_conn_checker: running check_connection() just_after_reconnection')
                    if not self.check_connection(just_after_reconnection=True):
                        self.close_connection()
                else:
                    # print('_conn_checker: running check_connection()')
                    if not self.check_connection():
                        self.close_connection()

            # delay
            # print('_conn_checker: delay')
            if not hasattr(self, '_check_connection_period') or not self._check_connection_period:
                self._check_connection_period = DEFAULT_CHECK_CONNECTION_PERIOD
            for _ in range(int(self._check_connection_period/0.1 + 0.5)):
                if not Global.run:
                    break
                sleep(0.1)

    # def request_handler(self, req):
    #     if False:
    #         # Add common requests for all modules here
    #         pass
    #     else:
    #         log.error('%s: Request handler error: Unknown request \'%s\'!' %\
    #                   (str(self.id), str(req)))

    def close_connection(self):
        if self._conn:
            try:
                self._conn.close()
            except:
                pass
            self._conn = None
            self.update_status('no_connection')

    def _get_connection(self):
        # if not Core.reserve_device(self.port):
        #     log.info('%s: Device %s could not be reserved in Core.' %\
        #              (str(self.id), str(self.port)))
        #     return False
        # else:
        #@@@ self.set_alarms('connection', False)
        #@@@ log.info('%s: Connection to %s established.' %\
        #@@@         (str(self.id), str(self.port)))
        # print('$ _get_connection: %s' % self._port)
        # print('_conn:', self._conn, '_port:', self._port, '_protocol:', self._protocol)
        if self._conn is None:
            if self._protocol == 'serial':
                if self._port is not None:
                    try:
                        self._conn = Sender(self._port) # TODO: engage self._connection_settings
                    except Exception as e:
                        log.error('Cannot get connection with %s: %s' %\
                          (str(self._port), str(e)))
                        return False
                    if not self._conn:
                        return False
                    return True
                else:
                    pass # TODO: just wait for device_finder to define self._port
            elif self._protocol == 'socket':
                pass # TODO: socket connection
                return False
            else:
                log.critical('Module is run with unsupported protocol %s' % str(self._protocol))
        return False

    # def find_device(self):
    #     pass

    # def find_device(self):
    #     dev_list = Core.get_device_list()
    #     if dev_list and len(dev_list) > 0:
    #         return dev_list
    #     else:
    #         return False

    # # What needs to be done after receiving Ctrl+C
    # def kill(self):
    #     return

    # def get_alarms(self):
    #     self._alarmsLock.acquire()
    #     alarms = self._alarms
    #     self._alarmsLock.release()
    #     return alarms

    # def set_alarms(self, alarm, on):
    #     self._alarmsLock.acquire()
    #     if on and alarm not in self._alarms:
    #         self._alarms.append(alarm)
    #     if not on and alarm in self._alarms:
    #         self._alarms.remove(alarm)
    #     self._alarmsLock.release()
    #     return

    def check_request_and_status(
            self, rq, appropriate_statuses):
        appropriate_statuses = to_tuple(appropriate_statuses)
        # check current request
        if self._request is not None:
            log.warning('request [%s] cannot be served '\
              'because of the previous [%s] request is still active' %
              (rq, self._request))
            ###@@@ self.update_status('failed previous request is active')
            return False
        sts = self._status
        for appr_sts in appropriate_statuses:
            if sts.startswith(appr_sts):
                # good
                self._request = rq
                break
        if not self._request:
            # maybe already in needed state
            log.warning('request [%s] cannot be served '\
              'because current state is [%s]' %
              (rq, sts))
            return False
        return True

