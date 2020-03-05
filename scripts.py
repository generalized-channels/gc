from bitcoinutils.script import Script
from identity import Id
import init
import consts
import scripts

init.init_network()

def get_script_ft_output(id_a: Id, id_b: Id) -> Script:
    scriptFToutput = Script([
                    id_a.pk.to_hex(), 'OP_CHECKSIGVERIFY', id_b.pk.to_hex(), 'OP_CHECKSIG']) # input: sigB, sigA
    return scriptFToutput

def get_script_lightning_locked(id_owner: Id, id_punisher: Id, hashedsecret, delta) -> Script:
    scriptLightningLocked = Script(['OP_DUP', id_punisher.pk.to_hex(), 'OP_CHECKSIG',
                    'OP_IF',
                        'OP_DROP', 'OP_HASH256', hashedsecret, 'OP_EQUALVERIFY',
                    'OP_ELSE',
                        id_owner.pk.to_hex(), 'OP_CHECKSIGVERIFY',
                        delta, 'OP_CHECKSEQUENCEVERIFY', 'OP_DROP',
                    'OP_ENDIF', 0x1]) # input: revsecret, sigPunisher OR (after some time delta) sigOwner
    return scriptLightningLocked

def get_script_split(id_a: Id, id_b: Id, id_as_a: Id, hashedsecret_rev_a, id_as_b: Id, hashedsecret_rev_b,  delta) -> Script:
    scriptCToutput = Script([id_a.pk.to_hex(), 'OP_CHECKSIG', 'OP_SWAP', id_b.pk.to_hex(), 'OP_CHECKSIG',
                    'OP_IF', # sigB?
                        'OP_IF', # sigA & sigB valid
                            delta, 'OP_CHECKSEQUENCEVERIFY', 'OP_DROP',
                        'OP_ELSE', # sigB valid (check if B has secrets of A)
                            id_as_a.pk.to_hex(), 'OP_CHECKSIGVERIFY',
                            'OP_HASH256', hashedsecret_rev_a, 'OP_EQUALVERIFY',
                        'OP_ENDIF',
                    'OP_ELSE',
                        'OP_IF', # sigA valid (check if A has secrets of B)
                            id_as_b.pk.to_hex(), 'OP_CHECKSIGVERIFY',
                            'OP_HASH256', hashedsecret_rev_b, 'OP_EQUALVERIFY',
                        'OP_ELSE',
                            'OP_RETURN',
                        'OP_ENDIF',
                    'OP_ENDIF', 0x1]) # input: secretRev_B, secretAS_B, 0, sigA 
                                      #    or: secretRev_A, secretAS_A, sigB, 0, 
                                      #    OR: (after some time delta:) sigB, sigA
    return scriptCToutput

def get_htlc_script(id_a: Id, id_b: Id, hashedsecret, hashedsecret_rev, delta) -> Script:
    scriptHTLC = Script(['OP_DUP', 'OP_HASH256', hashedsecret, 'OP_EQUAL',
                    'OP_IF',
                        'OP_DROP', id_b.pk.to_hex(), 'OP_CHECKSEQUENCEVERIFY',
                    'OP_ELSE',
                        id_a.pk.to_hex(), 'OP_CHECKSEQUENCEVERIFY',
                        'OP_HASH256', hashedsecret_rev,  'OP_EQUAL',
                        'OP_NOTIF',
                            delta, 'OP_CHECKSEQUENCEVERIFY', 'OP_DROP',
                        'OP_ENDIF',
                    'OP_ENDIF', 0x1]) # input: 
    return scriptHTLC