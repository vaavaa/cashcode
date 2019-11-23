#!/usr/bin/python3
"""
    Example code for resetting the USB ports
"""

import os
import fcntl
import subprocess
import re


# Equivalent of the _IO('U', 20) constant in the linux kernel.
USBDEVFS_RESET = ord('U') << (4*2) | 20


def get_buslist(filter=None):
    """
        Gets the devfs paths by scraping the output of the lsusb command
        The lsusb command outputs a list of USB devices attached to a computer
        in the format:
            Bus 002 Device 009: ID 16c0:0483 Van Ooijen Technische Informatica Teensyduino Serial
        The devfs path to these devices is:
            /dev/bus/usb/<busnum>/<devnum>
        So for the above device, it would be:
            /dev/bus/usb/002/009
        This function generates that path.
    """
    proc = subprocess.Popen(['lsusb'], stdout=subprocess.PIPE)
    out = proc.communicate()[0]
    if type(out) is bytes:
        out = out.decode('cp866')
    lines = out.split('\n')
    ret = list()
    for line in lines:
        parts = line.split()
        if len(parts) >= 4:
            if filter is None or re.search(filter, line, flags=re.I):
                #print(line, parts)
                bus = parts[1]
                dev = parts[3][:3]
                ret.append('/dev/bus/usb/%s/%s' % (bus, dev))
    return ret


def send_reset(dev_path):
    """
        Sends the USBDEVFS_RESET IOCTL to a USB device.

        dev_path - The devfs path to the USB device (under /dev/bus/usb/)
                   See get_teensy for example of how to obtain this.
    """
    fd = os.open(dev_path, os.O_WRONLY)
    try:
        fcntl.ioctl(fd, USBDEVFS_RESET, 0)
    finally:
        os.close(fd)

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        arg = sys.argv[-1]
        buslist = get_buslist(arg)
        if buslist:
            print('reset', buslist[0])
            send_reset(buslist[0])
    else:
        print('Usage: %s <filter>' % sys.argv[0])

