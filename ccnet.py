from core.Global import *
import serial
import datetime
import struct
from .utils import BillChannels #, Bills
###@@@ from core.sender import Sender
from core.module import Module
from glob import glob

MIN_CCNET_RESPONSE_LENGTH = 6


def brepr(v):
    if v:
        # w = ''
        # if len(v) > 0:
        #     if type(v[0]) is str:
        #         w = v[0]
        #         v = v[1:]
        # return w + ' ' + ' '.join(['%02X' % i for i in v]) + ' (' + str(bytes(v)) + ')'
        return '<' + ' '.join(['%02X' % i for i in v]) + ' (' + str(bytes(v)) + ')' + '>'
    else:
        return '<nothing>'


class CCNet(Module):
    SYNC = b'\x02'
    ADDR = b'\x03'
    ACK = b'\x00'
    NACK = b'\xff'

    RESPS = {
        ACK: 'ACK',
        NACK: 'NACK',
        b'\x10': 'Power up',
        b'\x11': 'Power bill',
        b'\x12\x00': 'Power w/bill in transport path',
        b'\x12\x01': 'Power w/bill in dispenser',
        b'\x13': 'Initialize',
        b'\x14': 'Idling',
        b'\x15': 'Accepting',
        b'\x17': 'Stacking',
        b'\x18': 'Returning',
        b'\x19': 'Unit disabled',
        b'\x1a': 'Holding',
        b'\x1b': 'Device busy',
        b'\x1c\x60': 'Rejecting due to insertion',
        b'\x1c\x61': 'Rejecting due to magnetic',
        b'\x1c\x62': 'Rejecting due to bill Remaining in the Head',
        b'\x1c\x63': 'Rejecting due to multiplying',
        b'\x1c\x64': 'Rejecting due to conveying',
        b'\x1c\x65': 'Rejecting due to identification1',
        b'\x1c\x66': 'Rejecting due to verification',
        b'\x1c\x67': 'Rejecting due to optic',
        b'\x1c\x68': 'Rejecting due to inhibit',
        b'\x1c\x69': 'Rejecting due to capacity',
        b'\x1c\x6a': 'Rejecting due to operation',
        b'\x1c\x6c': 'Rejecting due to length',
        b'\x1d': 'Dispensing',
        b'\x1e': 'Unloading',
        b'\x1f': 'Custom Returning',
        b'\x20': 'Recycling unloading',
        b'\x21': 'Setting cassette type',
        b'\x25': 'Dispenced',
        b'\x26': 'Unloaded',
        b'\x27': 'Custom bills returned',
        b'\x28': 'Recycling cassette unloaded',
        b'\x29': 'Set cassette type',
        b'\x30': 'Invalid command',
        b'\x41': 'Drop cassette full',
        b'\x42': 'Drop cassette out of position',
        b'\x43': 'Bill validator jammed',
        b'\x44': 'Cassette jammed',
        b'\x45': 'Cheated',
        b'\x46': 'Pause',
        b'\x47\x50': 'Stack motor failure',
        b'\x47\x51': 'Transport motor speed failure',
        b'\x47\x52': 'Transport motor failure',
        b'\x47\x53': 'Aligning motor failure',
        b'\x47\x54': 'Initial box status failure',
        b'\x47\x55': 'Optic canal failure',
        b'\x47\x56': 'Magnetic canal failure',
        b'\x47\x57': 'Cassette 1 motor failure',
        b'\x47\x58': 'Cassette 2 motor failure',
        b'\x47\x59': 'Cassette 3 motor failure',
        b'\x47\x5a': 'Bill-to-bill unit transport motor failure',
        b'\x47\x5b': 'Switch motor 1 failure',
        b'\x47\x5c': 'Switch motor 2 failure',
        b'\x47\x5d': 'Dispenser motor 1 failure',
        b'\x47\x5e': 'Dispenser motor 2 failure',
        b'\x47\x5f': 'Capacitance canal failure',
        b'\x48\x70': 'Bill jammed in cassette 1',
        b'\x48\x71': 'Bill jammed in cassette 2',
        b'\x48\x72': 'Bill jammed in cassette 3',
        b'\x48\x73': 'Bill jammed in transport path',
        b'\x48\x74': 'Bill jammed in switch',
        b'\x48\x75': 'Bill jammed in dispenser',
        b'\x80': 'Escrow position',
        b'\x81': 'Bill stacked',
        b'\x82': 'Bill returned',
    }
    CMDS = {
        'Reset': 0x30,
        'Get status': 0x31,
        'Set security': 0x32,
        'Poll': 0x33,
        'Enable bill types': 0x34,
        'Stack': 0x35,
        'Return': 0x36,
        'Identification': 0x37,
        'Hold': 0x38,
        'Cassette status': 0x3b,
        'Dispense': 0x3c,
        'Unload': 0x3d,
        'Escrow cassette status': 0x3e,
        'Escrow cassette unload': 0x3f,
        'Set cassette type': 0x40,
        'Get bill table': 0x41,
        'Download': 0x50,
    }

    country_prefix = list(b'RUB')

    ###@@@
    # nominal_list = {10: [0xE8, 0x3, 0x0, 0x0], 50: [0x88, 0x13, 0x0, 0x0],
    #                 100: [0x10, 0x27, 0x0, 0x0], 500: [0x50, 0xC3, 0x0, 0x0],
    #                 1000: [0xA0, 0x86, 0x1, 0x0], 5000: [0x20, 0xA1, 0x7, 0x0]}

    channel_map = {2: 10, 3: 50, 4: 100, 12: 200, 5: 500, 6: 1000, 13: 2000, 7: 5000}
    bill_channels = BillChannels(channel_map)


    def __init__(self):
        super().__init__()
        self._protocol = 'serial'

        self._essp_id = 0 # fixed addr
        self._dev_type = None

        ###@@@ self._port = '/dev/ttyUSB0' ###@@@!!!@@@### FIXME: HARDCODE

    def run(self):
        while Global.run:
            self.spin_once()
            sleep(0.888)

    def spin_once(self):

        if self._conn:
            self.poll()

        # sts = self._status
        # if sts:
        #     if sts.startswith('holding'):
        #         hold_resp = self.hold()
        #         if self.extract_resp_code(hold_resp) != 'ok':
        #             ###@@@ FIXME
        #             self.close_connection()
        #     elif sts.startswith('accepting'):
        #         poll_results = self.poll()
        #         if not poll_results or 'ok' not in poll_results:
        #             ###@@@ FIXME
        #             self.close_connection()
        #         # enable if disabled ### FIXME
        #         if 'disabled' in poll_results:
        #             self.enable()
        #         # look for credits
        #         for res in poll_results:
        #             if res.startswith('credit'):
        #                 # extract credit channel
        #                 chan = 0
        #                 try:
        #                     chan = int(res[len('credit'):].strip())
        #                 except Exception as e:
        #                     log.error(str(e))
        #                 if chan:
        #                     # get nominal and create event
        #                     nominal = self.bill_channels.get(chan)
        #                     self.append_event({nominal: 1})

        # # serve requests
        # sts = self._status
        # rq = self._request
        # if rq is not None and sts not in ('no_connection', 'initializing', None):
        #     # print('got a request:', rq)
        #     if rq.startswith('start'):
        #         resp = self.enable()
        #         if self.extract_resp_code(resp) == 'ok':
        #             self.update_status('accepting')
        #     elif rq.startswith('stop'):
        #         resp = self.disable()
        #         if self.extract_resp_code(resp) == 'ok':
        #             self.update_status('idle')
        #     #---
        #     if rq is not None:
        #         self._request = None

    def extract_resp_code(self, resp):
        if resp and len(resp) >= MIN_CCNET_RESPONSE_LENGTH:
            lngth = resp[2] - 5
            answer = resp[3: -2]
            if len(answer) != lngth:
                log.error('Got wrong response: ' + brepr(resp))
                return None
            ret = self.RESPS.get(answer[:2])
            if ret is None:
                ret = self.RESPS.get(answer[:1])
                if ret in ('ACK', 'NACK'):
                    if len(answer) != 1:
                        return None
            return ret

    def _initialize_device(self):
        self.update_status('initializing')
        self.reset()
        self.poll()
        sleep(0.25)
        self.poll()
        sleep(0.25)
        self.poll()
        sleep(0.25)
        self.poll()
        sleep(0.25)
        self.poll()
        self.get_validator_status()
        self.get_cassette_status()
        self.get_validator_info()
        self.disable()

        # self.enable(*self.bill_channels.ccnet_chan_mask_tuple)
        # ---
        self.update_status('idle')
        return True

    def check_connection(self, just_after_reconnection=False):
        if just_after_reconnection:
            inited = self._initialize_device()
            if not inited:
                return False
        #resp = self.check_host_protocol_version()
        #if resp and self.extract_resp_code(resp) == 'ok':
        #    return True
        return not False

    def reset(self):
        resp = self._execute(['Reset'])
        return self.extract_resp_code(resp) == 'ACK'

    def get_validator_status(self):
        return self._execute(['Get status'])

    def get_cassette_status(self):
        return self._execute(['Cassette status'])

    def get_bill_table(self):
        return self._execute(['Get bill table'])

    def get_validator_info(self):
        return self._execute(['Identification'])

    def enable(self, channels_mask):
        return self._execute(['Enable bill types'] + list(channels_mask))

    def disable(self):
        return self.enable((0, 0, 0))

    def poll(self):
        resp = self._execute(['Poll'])
        log.info('poll result: ' + self.extract_resp_code(resp))
        return self.extract_resp_code(resp)


    def reject(self):
        return self._execute(['Return'])

    def accept(self):
        return self._execute(['Stack'])

    def hold(self):
        result = self._execute(['Hold'])
        return result

    @staticmethod
    def chk(v):
        ret = 0
        for i in v:
            tmp = (ret ^ i) & 0xffff
            for j in range(8):
                if (tmp & 0x1):
                    tmp >>= 1
                    tmp ^= 0x08408
                else:
                    tmp >>= 1
            ret = tmp & 0xffff
        return ret.to_bytes(2, 'little')

    def _make_ccnet_packet(self, cmd):
        # if type(cmd) in (int, float):
        #     cmd = int(cmd)
        #     cmd = cmd.to_bytes(1, 'big')
        # elif type(cmd) is bytes:
        #     pass
        # elif type(cmd) is list:
        #     if len(cmd) > 0:
        #         if type(cmd[0]) is str:
        #             cmd[0] = self.CMDS.get(cmd[0]) or 0
        #         cmd = bytes(cmd)
        # elif type(cmd) is str:
        #     cmd = self.CMDS.get(cmd[0]) or 0
        #     cmd = cmd.to_bytes(1, 'big')

        payload = self.SYNC + self.ADDR + bytes([len(cmd) + 5]) + bytes(cmd)
        packet = payload + self.chk(payload)
        return packet

    def _execute(self, command):
        response = b''
        if self._conn and command:
            print('ccnet execute: locked????????????????????')
            with self._conn_lock:
                print('ccnet execute: locked!!!!!!!!!!!!!!')
                if type(command) is not list:
                    if type(command) in (int, float):
                        command = [int(command)]
                    if type(command) is str:
                        command = [command]
                    else:
                        command = list(command)
                log.debug(paint('-------- executing command %s' % str(command[0]), YELLOW))
                if len(command) > 0 and type(command[0]) is str:
                    cmd_code = self.CMDS.get(command[0])
                    if not cmd_code:
                        log.critical('Cannot find cmd code for %s command' % str(command[0]))
                    command[0] = cmd_code

                packet = self._make_ccnet_packet(command)
                #log.debug(paint('-------- request: %s' %\
                #               brepr(packet[3:-2]), CYAN))
                response = self._conn.send_packet(packet, total_timeout=0.44)
                color = GREEN
                if len(response) < MIN_CCNET_RESPONSE_LENGTH:
                    # not a packet
                    log.error('Got packet with insufficient length: %s' % brepr(response))
                    return b''
                resp_code = self.extract_resp_code(response)
                if command and command[0] == self.CMDS['Poll'] or resp_code == 'ACK':
                    log.debug(paint('-------- response: %s' %\
                      str(resp_code), color))
                else:
                    log.debug(paint('-------- response: %s' %\
                                   brepr(response[3:-2]), color))
                if response and resp_code != 'ACK':
                    # send ACK to validator
                    resp_on_ack = self._conn.send_packet(
                      self._make_ccnet_packet(self.ACK), total_timeout=0.140)
                    if resp_on_ack:
                        log.error('Device has sent a packet on host ACK: ' +
                          brepr(resp_on_ack))
        return response

    #==============================================================
    # REQUESTS
    #==============================================================

    def request_start_encashment(self):
        rq = 'start encashment'
        return self.check_request_and_status(rq, 'idle')

    def request_stop_encashment(self):
        rq = 'stop encashment'
        return self.check_request_and_status(rq, ('accepting', 'holding'))

