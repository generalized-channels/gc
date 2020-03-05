import binascii
import hashlib
from bitcoinutils.transactions import Transaction
import random

random.seed(7) # fix seed for showcase purposes

def gen_secret() -> str:
    """
        Replace this method with a secure random generator for any real world application
    """
    r = random.randrange(0, 255) # INSECURE, just for demo
    r = hex(r)[2:]
    if len(r) == 1:
        return f'0{r}'
    return r

def hash256(hexstring: str) -> str:
    data = binascii.unhexlify(hexstring)
    h1 = hashlib.sha256(data)
    h2 = hashlib.sha256(h1.digest())
    return h2.hexdigest()

def print_tx(tx: Transaction, name: str) -> None:
    print(f'{name}: {int(len(tx.serialize())/2)} Bytes')
    print(tx.serialize())
    print('----------------------------------')
