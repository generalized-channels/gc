from bitcoinutils.keys import P2pkhAddress, PrivateKey, PublicKey
import init
import consts

init.init_network()

class Id:
    """
    Helper class for handling identity related keys and addresses easily
    """
    def __init__(self, sk: str):
        self.sk = PrivateKey(secret_exponent=int(sk,16))
        self.pk = self.sk.get_public_key()
        self.addr = self.pk.get_address().to_string()
        self.p2pkh = P2pkhAddress(self.addr).to_script_pub_key()