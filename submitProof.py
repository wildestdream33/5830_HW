import json
from pathlib import Path
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware  # Necessary for POA chains

from web3.middleware import ExtraDataToPOAMiddleware

def merkle_assignment():
    num_of_primes = 8192

@@ -13,18 +12,16 @@ def merkle_assignment():
    leaves = convert_leaves(primes)
    tree = build_merkle(leaves)

    # Pick a random unclaimed prime index (change if needed)
    random_leaf_index = random.randint(0, num_of_primes - 1)
    # Pick a higher index to avoid already-claimed primes
    random_leaf_index = 1
    proof = prove_merkle(tree, random_leaf_index)

    challenge = ''.join(random.choice(string.ascii_letters) for i in range(32))
    challenge = ''.join(random.choice(string.ascii_letters) for _ in range(32))
    addr, sig = sign_challenge(challenge)

    if sign_challenge_verify(challenge, addr, sig):
        tx_hash = '0x'
        # Uncomment when ready to submit
        # tx_hash = send_signed_msg(proof, leaves[random_leaf_index])

        tx_hash = send_signed_msg(proof, leaves[random_leaf_index])
        print("Transaction sent, tx hash:", tx_hash)

def generate_primes(num_primes):
    primes_list = []

@@ -42,38 +39,31 @@ def generate_primes(num_primes):
        candidate += 1
    return primes_list


def convert_leaves(primes_list):
    return [Web3.to_bytes(p).rjust(32, b'\x00') for p in primes_list]

    return [int.to_bytes(p, 32, 'big') for p in primes_list]

def build_merkle(leaves):
    tree = [leaves]
    level = leaves
    while len(level) > 1:
        next_level = []
        for i in range(0, len(level), 2):
            left = level[i]
            if i + 1 < len(level):
                right = level[i + 1]
            else:
                right = left
            next_level.append(hash_pair(left, right))
        tree.append(next_level)
        level = next_level
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
    merkle_proof = []
    index = random_indx
    for level in merkle_tree[:-1]:  # Don't include root level
        sibling_index = index ^ 1  # Flip last bit to get sibling
        if sibling_index < len(level):
            merkle_proof.append(level[sibling_index])
    proof = []
    for layer in merkle_tree[:-1]:
        pair_index = index ^ 1
        if pair_index < len(layer):
            proof.append(layer[pair_index])
        index //= 2
    return merkle_proof

    return proof

def sign_challenge(challenge):
    acct = get_account()

@@ -82,8 +72,6 @@ def sign_challenge(challenge):
    signed = eth_account.Account.sign_message(eth_encoded_msg, acct.key)
    return addr, signed.signature.hex()



def send_signed_msg(proof, random_leaf):
    chain = 'bsc'
    acct = get_account()

@@ -91,26 +79,20 @@ def send_signed_msg(proof, random_leaf):
    w3 = connect_to(chain)

    contract = w3.eth.contract(address=address, abi=abi)
    nonce = w3.eth.get_transaction_count(acct.address)
    gas_price = w3.eth.gas_price

    txn = contract.functions.submit(proof, Web3.to_bytes(random_leaf).rjust(32, b'\x00')).build_transaction({
        'chainId': 97,
    # Build transaction
    tx = contract.functions.submit(proof, Web3.to_bytes(random_leaf)).build_transaction({
        'from': acct.address,
        'nonce': w3.eth.get_transaction_count(acct.address),
        'gas': 300000,
        'gasPrice': gas_price,
        'nonce': nonce
        'gasPrice': w3.eth.gas_price
    })

    signed_txn = w3.eth.account.sign_transaction(txn, acct.key)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    signed_tx = w3.eth.account.sign_transaction(tx, private_key=acct.key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    return tx_hash.hex()


# Helper functions remain unchanged
def connect_to(chain):
    if chain not in ['avax','bsc']:
        print(f"{chain} is not a valid option for 'connect_to()'")
        return None
    if chain == 'avax':
        api_url = f"https://api.avax-test.network/ext/bc/C/rpc"
    else:

@@ -119,39 +101,32 @@ def connect_to(chain):
    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    return w3


def get_account():
    cur_dir = Path(__file__).parent.absolute()
    with open(cur_dir.joinpath('sk.txt'), 'r') as f:
        sk = f.readline().rstrip()
    if sk[0:2] == "0x":
        sk = f.readline().strip()
    if sk.startswith("0x"):
        sk = sk[2:]
    return eth_account.Account.from_key(sk)


def get_contract_info(chain):
    contract_file = Path(__file__).parent.absolute() / "contract_info.json"
    if not contract_file.is_file():
        contract_file = Path(__file__).parent.parent.parent / "tests" / "contract_info.json"
    with open(contract_file, "r") as f:
        d = json.load(f)
        d = d[chain]
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







