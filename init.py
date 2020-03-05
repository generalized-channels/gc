import bitcoinutils.setup as setup
import consts

def init_network():
    if setup.get_network() == None:
        setup.setup(consts.network)