from .Global import *
from serial import Serial, PARITY_NONE, STOPBITS_ONE, EIGHTBITS
from threading import Lock
from time import sleep, time


def brepr(v):
    if v:
        return ' '.join(['%02X' % i for i in v])
    else:
        return '<nothing>'


class Sender:
    def __init__(self, port=None, more_verbose=False, **kwargs):
        self._port = port
        self._more_verbose = more_verbose

        baud = kwargs.get('baud') or kwargs.get('baudrate')
        self._baud = baud or 9600

        self._connLock = Lock()
        self.conn = None

    def _send_packet(self, packet=None, total_timeout=1.0, idle_timeout=0.1,
      read_after_send=True):
        if self.conn is None:
            self._open()
        if self.conn is None:
            return None

        if self._more_verbose:
            log.debug('%s: Sending packet %s' %\
                     (self._port, brepr(packet)))
        '''
        total_timeout --- first byte timeout
        idle_timeout --- between other bytes timeout
        '''

        #@@@ self._connLock.acquire()
        raw = b''

        # If no connection, do nothing.
        if self.conn is None:
            log.error('%s: No connection' % self._port)
            #@@@ self._connLock.release()
            return raw

        # Send packet
        if self.conn and packet:
            try:
                self.conn.write(packet)
            except Exception as e:
                #@@@ self._connLock.release()
                log.error(paint(str(e), RED))
                self._close()
                log.error('%s: Can\'t send packet' % self._port)
                return raw

        # Skip response
        if not read_after_send:
            #@@@ self._connLock.release()
            return raw

        #@@@ curr_timeout_val = tot_timeout # and then idle_time
        start_timeout = time()

        # Wait for the first bytes
        while Global.run:
            try:
                sleep(0.001)
                if (time() - start_timeout) > total_timeout:
                    if self._more_verbose:
                        log.debug('%s: 1) first bytes timeout!' % self._port)
                    break
                if self.conn.inWaiting():
                    start_timeout = time()
                    raw = raw + \
                      self.conn.read(self.conn.inWaiting())
                    if self._more_verbose:
                        log.debug('%s: 1) got first bytes: %s' %\
                                  (self._port, raw))
                    break # first bytes received
            except Exception as e:
                #@@@ self._connLock.release()
                log.error(paint(str(e), RED))
                self.close()
                log.error('%s: Packet error: Can`t read answer!' % self._port)
                return raw

        # Wait for the other bytes (by idle criteria)
        while Global.run:
            try:
                sleep(0.001)
                if (time() - start_timeout) > idle_timeout:
                    if self._more_verbose:
                        log.debug('%s: 2) idle timeout, got bytes: %s' %\
                                  (str(self._port), str(raw)))
                    break
                if self.conn.inWaiting():
                    start_timeout = time()
                    raw = raw + \
                      self.conn.read(self.conn.inWaiting())
            except Exception as e: # What is this?
                log.error(str(e))
        #@@@ self._connLock.release()
        return raw

    def send_packet(self, packet=None, total_timeout=1.0, idle_timeout=0.1,
      read_after_send=True):
        with self._connLock:
            return self._send_packet(packet, total_timeout, idle_timeout,
              read_after_send)

    def flush(self):
        with self._connLock:
            return self._flush()

    def _flush(self):
        if self.conn is None:
            self._open()
        if self.conn is None:
            return None
        r = self.conn.read(self.conn.inWaiting())
        if r:
            log.warning('%s: Flushed %s' %\
                     (self._port, brepr(r)))

    def _close(self):
        if self.conn:
            try:
                self.conn.close()
            except:
                pass
            self.conn = None

    def close(self):
        with self._connLock:
            self._close()

    def _open(self):
        if self.conn and self.conn.isOpen():
            # already opened
            return True
        # close if needed
        self._close()
        # reopen
        try:
            self.conn = Serial(port=self._port, baudrate=self._baud) # add kwargs
            return True
        except Exception as e:
            log.error(str(e))
            self._close()
            log.error('%s: Can\'t open port', self._port)
        return False

    def open(self):
        with self._connLock:
            return self._open()

