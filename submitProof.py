import eth_account
import random
import string
import json
from pathlib import Path
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware

def merkle_assignment():
    primes = generate_primes(8192)
    leaves = convert_leaves(primes)
    tree = build_merkle(leaves)
    # pick an unclaimed leaf at random (you can add logic to check on‐chain)
    random_leaf_index = random.randrange(len(leaves))
    proof = prove_merkle(tree, random_leaf_index)

    # sign a challenge so the autograder knows you control the key
    challenge = ''.join(random.choice(string.ascii_letters) for _ in range(32))
    addr, sig = sign_challenge(challenge)
    if sign_challenge_verify(challenge, addr, sig):
        send_signed_msg(proof, leaves[random_leaf_index])

def generate_primes(n):
    primes = []
    candidate = 2
    while len(primes) < n:
        is_prime = True
        for p in primes:
            if p * p > candidate:
                break
            if candidate % p == 0:
                is_prime = False
                break
        if is_prime:
            primes.append(candidate)
        candidate += 1
    return primes

def convert_leaves(primes):
    # pack each prime into a 32‐byte big‐endian word
    return [int.to_bytes(p, 32, 'big') for p in primes]

def build_merkle(leaves):
    tree = [leaves]
    level = leaves
    while len(level) > 1:
        nxt = []
        for i in range(0, len(level), 2):
            left = level[i]
            right = level[i+1] if i+1 < len(level) else left
            nxt.append(hash_pair(left, right))
        tree.append(nxt)
        level = nxt
    return tree

def prove_merkle(tree, index):
    proof = []
    for level in tree[:-1]:
        sibling = index ^ 1
        if sibling < len(level):
            proof.append(level[sibling])
        index //= 2
    return proof

def sign_challenge(challenge):
    acct = get_account()
    msg = eth_account.messages.encode_defunct(text=challenge)
    sig = eth_account.Account.sign_message(msg, acct.key)
    return acct.address, sig.signature.hex()

def send_signed_msg(proof, leaf):
    chain = 'bsc'
    acct = get_account()
    address, abi = get_contract_info(chain)
    w3 = connect_to(chain)
    contract = w3.eth.contract(address=address, abi=abi)

    tx = contract.functions.submit(proof, leaf).build_transaction({
        'from': acct.address,
        'nonce': w3.eth.get_transaction_count(acct.address),
        'gas': 300_000,
        'gasPrice': w3.to_wei('10', 'gwei'),
        'chainId': 97,
    })

    signed = w3.eth.account.sign_transaction(tx, acct.key)
    # <-- use raw_transaction, not rawTransaction
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    print("Submitted tx hash:", tx_hash.hex())

    # wait for it to be mined before exiting, so the autograder can see your claim
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    print(f"✔️ Mined in block {receipt.blockNumber}")
    return tx_hash.hex()


def connect_to(chain):
    url = ("https://data-seed-prebsc-1-s1.binance.org:8545/"
           if chain == 'bsc'
           else "https://api.avax-test.network/ext/bc/C/rpc")
    w3 = Web3(Web3.HTTPProvider(url))
    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    return w3

def get_account():
    key = Path(__file__).parent.joinpath('sk.txt').read_text().strip()
    if key.startswith('0x'):
        key = key[2:]
    return eth_account.Account.from_key(key)

def get_contract_info(chain):
    path = Path(__file__).parent / "contract_info.json"
    if not path.is_file():
        path = Path(__file__).parent.parent.parent / "tests" / "contract_info.json"
    data = json.loads(path.read_text())[chain]
    return data['address'], data['abi']

def sign_challenge_verify(challenge, addr, sig):
    msg = eth_account.messages.encode_defunct(text=challenge)
    return eth_account.Account.recover_message(msg, signature=sig) == addr

def hash_pair(a, b):
    # openzeppelin-style: sort before hashing
    if a < b:
        return Web3.solidity_keccak(['bytes32','bytes32'], [a,b])
    else:
        return Web3.solidity_keccak(['bytes32','bytes32'], [b,a])

if __name__ == "__main__":
    merkle_assignment()









