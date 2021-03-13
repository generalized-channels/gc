import bitcoinutils.setup as setup
from bitcoinutils.keys import P2pkhAddress, PrivateKey, PublicKey
from bitcoinutils.script import Script
from bitcoinutils.transactions import Transaction, TxInput, TxOutput, Sequence, TYPE_RELATIVE_TIMELOCK, TYPE_ABSOLUTE_TIMELOCK
import hashlib
import binascii
import consts
import init
import scripts
from helper import hash256, print_tx, gen_secret
from identity import Id
from abc import ABC, abstractmethod
from typing import List
import txs

init.init_network()

class State(ABC):
    @abstractmethod
    def get_state_transactions(self) -> List:
        pass
    
    @abstractmethod
    def get_balance_l(self) -> int:
        pass

    @abstractmethod
    def get_balance_r(self) -> int:
        pass

class LightningState(State):
    def __init__(self, ft: Transaction, id_l: Id, id_r: Id, val_l: int, val_r: int, fee: int, timelockCT: int=consts.timelockCT):
        self.ft = ft
        self.id_l = id_l
        self.id_r = id_r
        self.fee = fee
        self.timelockCT = timelockCT
        self.timelock = consts.timelock
        self.val_l = val_l
        self.val_r = val_r

        self.transactions = []

        secret_rev = gen_secret()

        ct_l = txs.get_standard_ct(TxInput(ft.get_txid(), 0), id_l, id_r, hash256(secret_rev), val_l, val_r, fee, l=True, timelock=0x2)
        ct_script = ct_l.outputs[0].script_pubkey.script
        ct_l_to_l = txs.get_standard_ct_spend(TxInput(ct_l.get_txid(),0), id_l, ct_script, int(val_l-0.5*self.fee), fee)
        ct_l_punish = txs.get_standard_ct_punish(TxInput(ct_l.get_txid(),0), self.id_r, ct_script, secret_rev, int(val_l-0.5*self.fee), fee)
        self.transactions.append(('CT_l',ct_l)) 
        self.transactions.append(('CT_l_to_l',ct_l_to_l)) 
        self.transactions.append(('CT_l_punish',ct_l_punish)) # in the real world, this is added only when this state is revoked

        secret_rev_r = gen_secret()
        ct_r = txs.get_standard_ct(TxInput(ft.get_txid(), 0), id_l, id_r, hash256(secret_rev_r), val_l, val_r, fee, l=False, timelock=0x2)
        ct_r_script = ct_r.outputs[0].script_pubkey.script
        ct_r_to_r = txs.get_standard_ct_spend(TxInput(ct_r.get_txid(),0), id_r, ct_r_script, int(val_r-0.5*self.fee), fee)
        ct_r_punish = txs.get_standard_ct_punish(TxInput(ct_r.get_txid(),0), self.id_l, ct_script, secret_rev_r, int(val_r-0.5*self.fee), fee)
        self.transactions.append(('CT_r',ct_l)) 
        self.transactions.append(('CT_r_to_r',ct_r_to_r)) 
        self.transactions.append(('CT_r_punish',ct_r_punish)) # in the real world, this is added only when this state is revoked

    def get_state_transactions(self):
        return self.transactions
    
    def get_balance_l(self):
        return self.val_l

    def get_balance_r(self):
        return self.val_r


class GeneralizedState(State):
    def __init__(self, ft: Transaction, id_l: Id, id_r: Id, secret_l, secret_r, val_l: int, val_r: int, fee: int, timelockCT: int=consts.timelockCT):
        self.ft = ft
        self.id_l = id_l
        self.id_r = id_r
        self.fee = fee
        self.timelockCT = timelockCT
        self.timelock = consts.timelock
        self.val_l = val_l
        self.val_r = val_r

        self.transactions = []

        id_as_l = Id('e12048ff047a0f15bcf977c86181828f5e05dbfe4cf1efe9af6362c8d53a00a3') # This is the sk that is leaking l's the adaptor signature in the real world
        secret_rev_l = gen_secret()
        id_as_r = Id('e12048ff047a0f15bcf977c86181828f5e05dbfe4cf1eee9af6362c8d53a02c1') # This is the sk that is leaking r's the adaptor signature in the real world
        secret_rev_r = gen_secret()

        ct = txs.get_gen_ct_tx(TxInput(ft.get_txid(), 0), id_l, id_r, id_as_l, hash256(secret_rev_l), id_as_r, hash256(secret_rev_r), val_l+val_r, fee, 0x2)
        ct_script = ct.outputs[0].script_pubkey.script
        ct_punish_l = txs.get_gen_punish_tx(TxInput(ct.get_txid(),0), id_l, ct_script, id_as_r, secret_rev_r, val_l+val_r-self.fee, fee, l=True)
        ct_punish_r = txs.get_gen_punish_tx(TxInput(ct.get_txid(),0), id_r, ct_script, id_as_l, secret_rev_l, val_l+val_r-self.fee, fee, l=False)
        ct_spend = txs.get_gen_split_tx(TxInput(ct.get_txid(),0), id_l, id_r, ct_script, int(val_l-0.5*fee), int(val_r-0.5*fee), fee)
        self.transactions.append(('CT',ct)) 
        self.transactions.append(('CT spend', ct_spend)) 
        self.transactions.append(('CT_punish_l',ct_punish_l)) # in the real world, the secret for this transaction is shared when the state is revoked
        self.transactions.append(('CT_punish_r',ct_punish_r)) # in the real world, the secret for this transaction is shared when the state is revoked


    def get_state_transactions(self):
        return self.transactions
    
    def get_balance_l(self):
        return self.val_l

    def get_balance_r(self):
        return self.val_r


"""
        ###test
        x = 0.0004
        secret_htlc = gen_secret()
        ct_htlc = txs.get_htlc_ct(TxInput(ft.get_txid(), 0), id_l, id_r, hash256(secret_htlc), hash256(secret_rev), val_l-x, val_r, x, fee, l=True, timelock=0x2)
        print_tx(ct_htlc, 'CT_HTLC')
        htlc = txs.get_htlc(TxInput(ct_htlc.get_txid(), 0), id_l, id_r, secret_htlc, hash256(secret_rev), val_l, val_r, fee, l=True, timelock=0x02)
        print_tx(htlc, 'HTLC')
        ###test
"""
