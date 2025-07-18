import eth_account
import random
import string
import json
from pathlib import Path
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware  # Necessary for POA chains


# ────────────────────────────── MAIN FLOW ──────────────────────────────
def merkle_assignment():
    num_of_primes = 8192
    primes = generate_primes(num_of_primes)          # 1. first 8192 primes
    leaves = convert_leaves(primes)                  # 2. primes → bytes32 leaves
    tree = build_merkle(leaves)                      # 3. build merkle tree

    random_leaf_index = 1                            # choose an index ≥1 (0 is likely claimed)
    proof = prove_merkle(tree, random_leaf_index)    # 4. generate proof for that leaf

    # 5. sign a random challenge so autograder can verify you own the address
    challenge = ''.join(random.choice(string.ascii_letters) for _ in range(32))
    addr, sig = sign_challenge(challenge)

    if sign_challenge_verify(challenge, addr, sig):
        # 6. submit the proof on-chain (requires BNB testnet funds)
        tx_hash = send_signed_msg(proof, leaves[random_leaf_index])
        print("Submitted! TX hash:", tx_hash)


# ──────────────────────────── CORE FUNCTIONS ───────────────────────────
def generate_primes(num_primes):
    primes_list, candidate = [], 2
    while len(primes_list) < num_primes:
        for p in primes_list:
            if p * p > candidate:
                break
            if candidate % p == 0:
                break
        else:
            primes_list.append(candidate)
        candidate += 1
    return primes_list


def convert_leaves(primes_list):
    # Convert each prime to 32-byte big-endian bytes
    return [int.to_bytes(p, 32, 'big') for p in primes_list]


def build_merkle(leaves):
    tree = [leaves]
    level = leaves
    while len(level) > 1:
        nxt = []
        for i in range(0, len(level), 2):
            left = level[i]
            right = level[i + 1] if i + 1 < len(level) else left
            nxt.append(hash_pair(left, right))
        tree.append(nxt)
        level = nxt
    return tree


def prove_merkle(merkle_tree, index):
    proof = []
    for level in merkle_tree[:-1]:           # exclude root
        sibling_index = index ^ 1
        if sibling_index < len(level):
            proof.append(level[sibling_index])
        index //= 2
    return proof


def sign_challenge(challenge):
    acct = get_account()
    message = eth_account.messages.encode_defunct(text=challenge)
    signed = eth_account.Account.sign_message(message, acct.key)
    return acct.address, signed.signature.hex()


def send_signed_msg(proof, random_leaf):
    """
    Build, sign, and send the transaction that calls `submit(proof, leaf)`
    on the BSC-testnet contract.
    """
    chain = 'bsc'
    acct = get_account()
    address, abi = get_contract_info(chain)
    w3 = connect_to(chain)
    contract = w3.eth.contract(address=address, abi=abi)

    nonce = w3.eth.get_transaction_count(acct.address)
    txn = contract.functions.submit(proof, random_leaf).build_transaction({
        'from':   acct.address,
        'chainId': 97,                       # BSC testnet chain-id
        'gas':    300_000,
        'gasPrice': w3.to_wei('10', 'gwei'),
        'nonce':  nonce
    })

    # IMPORTANT: sign with w3.eth.account to get a SignedTransaction that has rawTransaction
    signed_txn = w3.eth.account.sign_transaction(txn, acct.key)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)

    print(f"✅ TX submitted: https://testnet.bscscan.com/tx/{tx_hash.hex()}")
    return tx_hash.hex()


# ──────────────────────────── HELPER FUNCTIONS ─────────────────────────
def connect_to(chain):
    if chain not in ['avax', 'bsc']:
        raise ValueError("chain must be 'avax' or 'bsc'")
    api_url = ("https://api.avax-test.network/ext/bc/C/rpc"
               if chain == 'avax'
               else "https://data-seed-prebsc-1-s1.binance.org:8545/")
    w3 = Web3(Web3.HTTPProvider(api_url))
    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    return w3


def get_account():
    cur_dir = Path(__file__).parent.absolute()
    sk = (cur_dir / 'sk.txt').read_text().strip()
    if sk.startswith("0x"):
        sk = sk[2:]
    return eth_account.Account.from_key(sk)


def get_contract_info(chain):
    contract_file = Path(__file__).parent / "contract_info.json"
    if not contract_file.is_file():
        contract_file = Path(__file__).parent.parent.parent / "tests" / "contract_info.json"
    d = json.loads(contract_file.read_text())[chain]
    return d['address'], d['abi']


def sign_challenge_verify(challenge, addr, sig):
    msg = eth_account.messages.encode_defunct(text=challenge)
    return eth_account.Account.recover_message(msg, signature=sig) == addr


def hash_pair(a, b):
    # Sort before hashing to match OpenZeppelin's sorted pairs convention
    if a < b:
        return Web3.solidity_keccak(['bytes32', 'bytes32'], [a, b])
    else:
        return Web3.solidity_keccak(['bytes32', 'bytes32'], [b, a])


# ────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    merkle_assignment()





