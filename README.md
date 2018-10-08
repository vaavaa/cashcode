from cashcode import ccnet
cc = ccnet.CCNet('/dev/ttyS1')
cc.launch()
cc.get_validator_info()

