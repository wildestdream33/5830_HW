import eth_account
import random
import string
import json
from pathlib import Path
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware

def merkle_assignment():
    num_of_primes = 8192
    primes = generate_primes(num_of_primes)
    leaves = convert_leaves(primes)
    tree = build_merkle(leaves)

    # Pick a higher index to avoid already-claimed primes
    random_leaf_index = 1
    proof = prove_merkle(tree, random_leaf_index)

    challenge = ''.join(random.choice(string.ascii_letters) for _ in range(32))
    addr, sig = sign_challenge(challenge)

    if sign_challenge_verify(challenge, addr, sig):
        tx_hash = send_signed_msg(proof, leaves[random_leaf_index])
        print("Transaction sent, tx hash:", tx_hash)

def generate_primes(num_primes):
    primes_list = []
    candidate = 2
    while len(primes_list) < num_primes:
        is_prime = True
        for p in primes_list:
            if p * p > candidate:
                break
            if candidate % p == 0:
                is_prime = False
                break
        if is_prime:
            primes_list.append(candidate)
        candidate += 1
    return primes_list

def convert_leaves(primes_list):
    return [int.to_bytes(p, 32, 'big') for p in primes_list]

def build_merkle(leaves):
    tree = [leaves]
    current_layer = leaves
    while len(current_layer) > 1:
        next_layer = []
        for i in range(0, len(current_layer), 2):
            a = current_layer[i]
            b = current_layer[i+1] if i+1 < len(current_layer) else a
            next_layer.append(hash_pair(a, b))
        tree.append(next_layer)
        current_layer = next_layer
    return tree

def prove_merkle(merkle_tree, random_indx):
    index = random_indx
    proof = []
    for layer in merkle_tree[:-1]:
        pair_index = index ^ 1
        if pair_index < len(layer):
            proof.append(layer[pair_index])
        index //= 2
    return proof

def sign_challenge(challenge):
    acct = get_account()
    addr = acct.address
    eth_encoded_msg = eth_account.messages.encode_defunct(text=challenge)
    signed = eth_account.Account.sign_message(eth_encoded_msg, acct.key)
    return addr, signed.signature.hex()

def send_signed_msg(proof, random_leaf):
    """
        Takes a Merkle proof of a leaf, and that leaf (in bytes32 format)
        builds signs and sends a transaction claiming that leaf (prime)
        on the contract
    """
    chain = 'bsc'
    acct = get_account()
    address, abi = get_contract_info(chain)
    w3 = connect_to(chain)

    contract = w3.eth.contract(address=address, abi=abi)

    nonce = w3.eth.get_transaction_count(acct.address)

    txn = contract.functions.submit(proof, random_leaf).build_transaction({
        'chainId': 97,
        'gas': 300000,
        'gasPrice': w3.to_wei('10', 'gwei'),
        'nonce': nonce
    })

    signed_txn = w3.eth.account.sign_transaction(txn, acct.key)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)

    print(f"Transaction sent! TX Hash: {tx_hash.hex()}")
    return tx_hash.hex()


def connect_to(chain):
    if chain == 'avax':
        api_url = f"https://api.avax-test.network/ext/bc/C/rpc"
    else:
        api_url = f"https://data-seed-prebsc-1-s1.binance.org:8545/"
    w3 = Web3(Web3.HTTPProvider(api_url))
    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    return w3

def get_account():
    cur_dir = Path(__file__).parent.absolute()
    with open(cur_dir.joinpath('sk.txt'), 'r') as f:
        sk = f.readline().strip()
    if sk.startswith("0x"):
        sk = sk[2:]
    return eth_account.Account.from_key(sk)

def get_contract_info(chain):
    contract_file = Path(__file__).parent.absolute() / "contract_info.json"
    with open(contract_file, "r") as f:
        d = json.load(f)[chain]
    return d['address'], d['abi']

def sign_challenge_verify(challenge, addr, sig):
    eth_encoded_msg = eth_account.messages.encode_defunct(text=challenge)
    return eth_account.Account.recover_message(eth_encoded_msg, signature=sig) == addr

def hash_pair(a, b):
    if a < b:
        return Web3.solidity_keccak(['bytes32', 'bytes32'], [a, b])
    else:
        return Web3.solidity_keccak(['bytes32', 'bytes32'], [b, a])

if __name__ == "__main__":
    merkle_assignment()



