#!/usr/bin/python3
from core.Global import *
from cashcode import ccnet
from cashcode.utils import Bills
from sys import argv

if __name__ == '__main__':
    port = '/dev/ttyUSB0'
    if len(argv) > 1:
        port = argv[1] # for example: '/dev/ttyUSB0'
    cc = ccnet.CCNet(port)
    cc.launch()

    # start encashment
    bills = Bills()
    while not cc.request_start_encashment():
        if not Global.run: break
        cc.get_status()
        sleep(1.8)
    # do encashment
    for _ in range(120): # about 2 minutes
        if not Global.run: break
        bills.add(cc.get_events())
        sts = cc.get_status()
        if sts == 'idle':
            # restart encashment
            while not cc.request_start_encashment():
                if not Global.run: break
                cc.get_status()
                sleep(1.8)
        sleep(1)
    # stop encashment
    while not cc.request_stop_encashment():
        if not Global.run: break
        bills.add(cc.get_events())
        cc.get_status()
        sleep(1.8)
    # dummy
    for _ in range(3):
        if not Global.run: break
        bills.add(cc.get_events())
        cc.get_status()
        sleep(1)
    # break
    Global.run = False
    sleep(2)

    # reports
    print('='*80)
    print('='*80)
    print('ENCASHMENT COMPLETED:')
    print('  total sum:', bills.sum)
    print('   nominals:', bills.nominals)
    print('    details:')
    print(bills)
    print('='*80)
    print('='*80)
    sleep(1.2)
    input('                             Press any key...')

