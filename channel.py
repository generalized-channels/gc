from identity import Id
from state import State, LightningState, GeneralizedState
from bitcoinutils.transactions import Transaction, TxInput, TxOutput
from bitcoinutils.script import Script
import scripts
import consts
import init
from helper import gen_secret

LIGHTNING_STATE = 0
GENERALIZED_STATE = 1

init.init_network()

class Channel:
    def __init__(self, id_l, id_r, fee, ctype: int = GENERALIZED_STATE) -> None:
        self.id_l = id_l
        self.id_r = id_r
        self.val_l = 0
        self.val_r = 0
        self.fee = fee
        self.state = None
        self.state_list = []
        self.close_tx = None

    def set_ft(self, ft: Transaction, val_l: float, val_r: float) -> None:
        self.ft = ft
        self.val_l = val_l
        self.val_r = val_r
    
    def create_ft(self, input_l: TxInput, input_r: TxInput, val_l: float, val_r: float) -> Transaction:
        txs_in = [input_l, input_r]
        tx_out = TxOutput(val_l + val_r - self.fee, scripts.get_script_ft_output(self.id_l, self.id_r))
        tx = Transaction(txs_in, [tx_out])

        sig_l = self.id_l.sk.sign_input(tx, 0 , self.id_l.p2pkh)
        sig_r = self.id_r.sk.sign_input(tx, 1 , self.id_r.p2pkh)

        input_l.script_sig = Script([sig_l, self.id_l.pk.to_hex()])
        input_r.script_sig = Script([sig_r, self.id_r.pk.to_hex()])
        return tx

    def create_close_tx(self, valA: float, valB: float) -> Transaction:
        tx_in = TxInput(self.ft.get_txid(), 0)
        tx_out_l = TxOutput(valA - self.fee, self.id_l.p2pkh)
        tx_out_r = TxOutput(valB - self.fee, self.id_r.p2pkh)

        tx = Transaction([tx_in], [tx_out_l, tx_out_r])

        sig_l = self.id_l.sk.sign_input(tx, 0 , scripts.get_script_ft_output(self.id_l, self.id_r))
        sig_r = self.id_r.sk.sign_input(tx, 0 , scripts.get_script_ft_output(self.id_l, self.id_r))

        tx_in.script_sig = Script([sig_r, sig_l])
        return tx

    @staticmethod
    def from_ft(id_l: Id, id_r: Id, ft: Transaction, val_l: float, val_r: float, fee: float, ctype = GENERALIZED_STATE) -> 'Channel':
        channel = Channel(id_l, id_r, fee, ctype)
        channel.set_ft(ft, val_l, val_r)
        channel.update(val_l, val_r, ctype)
        return channel
    
    @staticmethod
    def from_inputs(id_l: Id, id_r: Id, input_l: TxInput, input_r: TxInput, val_l: float, val_r: float, fee: float, ctype = GENERALIZED_STATE) -> 'Channel':
        channel = Channel(id_l, id_r, fee, ctype)
        ft = channel.create_ft(input_l, input_r, val_l, val_r)
        channel.set_ft(ft, val_r, val_r)
        channel.update(val_l, val_r, ctype)
        return channel

    def new_state(self, type: int, tx_in, val_l: float, val_r: float, id_ingrid: Id=None) -> State:
        if type == LIGHTNING_STATE:
            return LightningState(tx_in, self.id_l, self.id_r, val_l-self.fee/2, val_r-self.fee/2, self.fee)
        elif type == GENERALIZED_STATE:
            secret_l = gen_secret()
            secret_r = gen_secret()
            return GeneralizedState(tx_in, self.id_l, self.id_r, secret_l, secret_r, val_l-self.fee/2, val_r-self.fee/2, self.fee)
        else:
            raise ValueError(f'Type {type} not recognized.')

    def update(self, val_l, val_r, ctype: int, id_ingrid: Id=None):
        if self.state != None:
            self.state_list.append(self.state)
        self.state = self.new_state(ctype, self.ft, val_l, val_r, id_ingrid)

    def close(self, val_l, val_r):
        self.state_list.append(self.state)
        self.state = None
        self.close_tx = self.create_close_tx(val_l, val_r)

