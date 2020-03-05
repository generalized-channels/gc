from bitcoinutils.transactions import Transaction, TxOutput, TxInput, Sequence, TYPE_RELATIVE_TIMELOCK, TYPE_ABSOLUTE_TIMELOCK
from bitcoinutils.script import Script
from identity import Id
import init
import scripts
import consts

init.init_network()

### Transactions for lightning

def get_standard_ct(tx_in: TxInput, id_l: Id, id_r: Id, hashed_secret, val_l: float, val_r: float, fee: float, l: bool, timelock) -> Transaction:
    if l:
        tx_out0 = TxOutput(val_l-fee/2, scripts.get_script_lightning_locked(id_l, id_r, hashed_secret, timelock)) # output to l
        tx_out1 = TxOutput(val_r-fee/2, id_r.p2pkh) # output to r
    else:
        tx_out0 = TxOutput(val_r-fee/2, scripts.get_script_lightning_locked(id_r, id_l, hashed_secret, timelock)) # output to r
        tx_out1 = TxOutput(val_l-fee/2, id_l.p2pkh) # output to l

    tx = Transaction([tx_in], [tx_out0, tx_out1])

    scriptFToutput = scripts.get_script_ft_output(id_l, id_r)

    sig_l = id_l.sk.sign_input(tx, 0, scriptFToutput)
    sig_r = id_r.sk.sign_input(tx, 0, scriptFToutput)

    tx_in.script_sig = Script([sig_r, sig_l])

    return tx

def get_standard_ct_spend(tx_in: TxInput, payee: Id, script_ct: Script, val: float, fee: float)-> Transaction:

    tx_out = TxOutput(val-fee, payee.p2pkh)
    tx = Transaction([tx_in], [tx_out])
    
    sig = payee.sk.sign_input(tx, 0 , Script(script_ct))

    tx_in.script_sig = Script([sig])
    
    return tx

def get_standard_ct_punish(tx_in: TxInput, payee: Id, script_ct: Script, secret, val: float, fee: float)-> Transaction:

    tx_out = TxOutput(val-fee, payee.p2pkh)
    tx = Transaction([tx_in], [tx_out])
    
    sig = payee.sk.sign_input(tx, 0 , Script(script_ct))

    tx_in.script_sig = Script([secret, sig])
    
    return tx

### Generalized construction

def get_gen_ct_tx(tx_in: TxInput, id_l: Id, id_r: Id, id_as_l: Id, hashed_secret_rev_l, id_as_r: Id, hashed_secret_rev_r, val: float, fee: float, timelock: int) -> Transaction:
    timelock = 0x2
    tx_out = TxOutput(val-fee, scripts.get_script_split(id_l, id_r, id_as_l, hashed_secret_rev_l, id_as_r, hashed_secret_rev_r, timelock))
    tx = Transaction([tx_in], [tx_out])

    scriptFToutput = scripts.get_script_ft_output(id_l, id_r)

    sig_l = id_l.sk.sign_input(tx, 0 , scriptFToutput)
    sig_r = id_r.sk.sign_input(tx, 0 , scriptFToutput)

    tx_in.script_sig = Script([sig_r, sig_l])

    return tx

def get_gen_split_tx(tx_in: TxInput, id_l: Id, id_r: Id, script: Script, val_l: int, val_r, fee: float) -> Transaction:
    tx_out0 = TxOutput(val_l-0.5*fee, id_l.p2pkh)
    tx_out1 = TxOutput(val_r-0.5*fee, id_r.p2pkh)
    tx = Transaction([tx_in], [tx_out0, tx_out1])

    sig_l = id_l.sk.sign_input(tx, 0, Script(script))
    sig_r = id_r.sk.sign_input(tx, 0, Script(script))

    tx_in.script_sig = Script([sig_r, sig_l])

    return tx

def get_gen_punish_tx(tx_in: TxInput, payee: Id, script: Script, id_as: Id, secret_rev, val: int, fee: float, l: bool) -> Transaction:
    tx_out = TxOutput(val-fee, payee.p2pkh)
    tx = Transaction([tx_in], [tx_out])

    sig = payee.sk.sign_input(tx, 0, Script(script))
    sig_as = id_as.sk.sign_input(tx, 0, Script(script))

    if l:
        tx_in.script_sig = Script([secret_rev, sig_as, 0x0, sig])
    else:
        tx_in.script_sig = Script([secret_rev, sig_as, sig, 0x0])

    return tx

### Test HTLC construction (just for measuring)

def get_htlc(tx_in: TxInput, id_l: Id, id_r: Id, secret, hashed_secret, val_l: float, val_r: float, fee: float, l: bool, timelock) -> Transaction:
    tx_out = TxOutput(val_l-fee/2, scripts.get_script_lightning_locked(id_l, id_r, hashed_secret, timelock)) # output to l

    tx = Transaction([tx_in], [tx_out])

    scriptFToutput = scripts.get_script_ft_output(id_l, id_r)

    sig = id_l.sk.sign_input(tx, 0, scriptFToutput) # referenced tx is ft

    tx_in.script_sig = Script([sig, secret])

    return tx

def get_htlc_ct(tx_in: TxInput, id_l: Id, id_r: Id, hashed_secret, hashed_secret2, val_l: float, val_r: float, x, fee: float, l: bool, timelock) -> Transaction:
    if l:
        tx_out0 = TxOutput(val_l-fee/2, scripts.get_script_lightning_locked(id_l, id_r, hashed_secret, timelock)) # output to l
        tx_out1 = TxOutput(val_l-fee/2, scripts.get_htlc_script(id_l, id_r, hashed_secret, hashed_secret2, timelock)) # HTLC output
        tx_out2 = TxOutput(val_r-fee/2, id_r.p2pkh) # output to r
    else:
        tx_out0 = TxOutput(val_r-fee/2, scripts.get_script_lightning_locked(id_r, id_l, hashed_secret, timelock)) # output to r
        tx_out1 = TxOutput(val_l-fee/2, scripts.get_htlc_script(id_l, id_r, hashed_secret, hashed_secret2, timelock)) # HTLC output
        tx_out2 = TxOutput(val_l-fee/2, id_l.p2pkh) # output to l

    tx = Transaction([tx_in], [tx_out0, tx_out1, tx_out2])

    scriptFToutput = scripts.get_script_ft_output(id_l, id_r)

    sig_l = id_l.sk.sign_input(tx, 0, scriptFToutput)
    sig_r = id_r.sk.sign_input(tx, 0, scriptFToutput)

    tx_in.script_sig = Script([sig_r, sig_l])

    return tx