import eth_account
import random
import string
import json
from pathlib import Path
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware  # Necessary for POA chains


def merkle_assignment():
    """
        The only modifications you need to make to this method are to assign
        your "random_leaf_index" and uncomment the last line when you are
        ready to attempt to claim a prime. You will need to complete the
        methods called by this method to generate the proof.
    """
    # Generate the list of primes as integers
    num_of_primes = 8192
    primes = generate_primes(num_of_primes)

    # Create a version of the list of primes in bytes32 format
    leaves = convert_leaves(primes)

    # Build a Merkle tree using the bytes32 leaves as the Merkle tree's leaves
    tree = build_merkle(leaves)

    # Select a random leaf and create a proof for that leaf
    while True:
        random_leaf_index = random.randint(0, num_of_primes - 1)
        address, abi = get_contract_info("bsc")
        w3 = connect_to("bsc")
        contract = w3.eth.contract(address=address, abi=abi)
        leaf_prime = primes[random_leaf_index]
        current_owner = contract.functions.getOwnerByPrime(leaf_prime).call()
        if int(current_owner, 16) == 0:
            break

    proof = prove_merkle(tree, random_leaf_index)

    # This is the same way the grader generates a challenge for sign_challenge()
    challenge = ''.join(random.choice(string.ascii_letters) for i in range(32))
    # Sign the challenge to prove to the grader you hold the account
    addr, sig = sign_challenge(challenge)

    if sign_challenge_verify(challenge, addr, sig):
        tx_hash = send_signed_msg(proof, leaves[random_leaf_index])
        print("TX hash:", tx_hash)


def generate_primes(num_primes):
    primes_list = []
    n = 2
    while len(primes_list) < num_primes:
        for p in primes_list:
            if n % p == 0:
                break
        else:
            primes_list.append(n)
        n += 1
    return primes_list


def convert_leaves(primes_list):
    return [Web3.solidity_keccak(['uint256'], [p]) for p in primes_list]


def build_merkle(leaves):
    tree = [leaves]
    current = leaves
    while len(current) > 1:
        new_level = []
        for i in range(0, len(current), 2):
            if i + 1 < len(current):
                new_level.append(hash_pair(current[i], current[i + 1]))
            else:
                new_level.append(current[i])
        tree.append(new_level)
        current = new_level
    return tree


def prove_merkle(merkle_tree, random_indx):
    merkle_proof = []
    index = random_indx
    for level in merkle_tree[:-1]:
        sibling_index = index ^ 1
        if sibling_index < len(level):
            merkle_proof.append(level[sibling_index])
        index //= 2
    return merkle_proof


def sign_challenge(challenge):
    acct = get_account()
    addr = acct.address
    eth_sk = acct.key
    eth_encoded_msg = eth_account.messages.encode_defunct(text=challenge)
    eth_sig_obj = eth_account.Account.sign_message(eth_encoded_msg, eth_sk)
    return addr, eth_sig_obj.signature.hex()


def send_signed_msg(proof, random_leaf):
    chain = 'bsc'
    acct = get_account()
    address, abi = get_contract_info(chain)
    w3 = connect_to(chain)
    contract = w3.eth.contract(address=address, abi=abi)
    nonce = w3.eth.get_transaction_count(acct.address)
    txn = contract.functions.submit(proof, random_leaf).build_transaction({
        'from': acct.address,
        'nonce': nonce,
        'gas': 500000,
        'gasPrice': w3.to_wei('10', 'gwei')
    })
    signed_txn = w3.eth.account.sign_transaction(txn, private_key=acct.key)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    return tx_hash.hex()


# Helper functions that do not need to be modified
def connect_to(chain):
    if chain not in ['avax','bsc']:
        print(f"{chain} is not a valid option for 'connect_to()'")
        return None
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
        sk = f.readline().rstrip()
    if sk[0:2] == "0x":
        sk = sk[2:]
    return eth_account.Account.from_key(sk)


def get_contract_info(chain):
    contract_file = Path(__file__).parent.absolute() / "contract_info.json"
    if not contract_file.is_file():
        contract_file = Path(__file__).parent.parent.parent / "tests" / "contract_info.json"
    with open(contract_file, "r") as f:
        d = json.load(f)
        d = d[chain]
    return d['address'], d['abi']


def sign_challenge_verify(challenge, addr, sig):
    eth_encoded_msg = eth_account.messages.encode_defunct(text=challenge)
    if eth_account.Account.recover_message(eth_encoded_msg, signature=sig) == addr:
        print(f"Success: signed the challenge {challenge} using address {addr}!")
        return True
    else:
        print(f"Failure: The signature does not verify!")
        print(f"signature = {sig}\naddress = {addr}\nchallenge = {challenge}")
        return False


def hash_pair(a, b):
    if a < b:
        return Web3.solidity_keccak(['bytes32', 'bytes32'], [a, b])
    else:
        return Web3.solidity_keccak(['bytes32', 'bytes32'], [b, a])


if __name__ == "__main__":
    merkle_assignment()

