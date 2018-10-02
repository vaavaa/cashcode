from serial import Serial
from time import sleep


def bre(v):
    if v:
        return ' '.join(['%02X' % i for i in v])
    else:
        return '<nothing>'

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

def mkpk(cmd, data=b''):
    ret = b'\x02\x03\x06' + cmd.to_bytes(1, 'big')
    c = chk(ret)
    return ret + c

s = Serial('/dev/ttyS1')

rs = mkpk(b'0')
sts = mkpk(b'1')
poll = mkpk(b'3')
ena = mkpk(b'4\xff\xff\xff\x00\x00\x00')
stack = mkpk(b'5')

# s.write(rs)
# s.write(stack)
# s.write(sts)
# s.write(ena)

s.write(rs)
r = s.read(s.inWaiting()); print(bre(r))

while True:
    s.write(poll)
    sleep(0.5)
    r = s.read(s.inWaiting())
    print(bre(r))

s.close()

