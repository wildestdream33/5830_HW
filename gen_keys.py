from web3 import Web3
from eth_account.messages import encode_defunct
import eth_account
import os


def sign_message(challenge, filename="secret_key.txt"):
    """
    challenge - byte string
    filename - filename of the file that contains your account secret key
    To pass the tests, your signature must verify, and the account you use
    must have testnet funds on both the bsc and avalanche test networks.
    """
    # This code will read your "secret_key.txt" file
    # If the file is empty, it will raise an exception
    if not os.path.exists(filename) or os.stat(filename).st_size == 0:
        # If file doesn't exist or is empty, generate a new key
        acct = eth_account.Account.create()
        with open(filename, "w") as f:
            f.write(acct.key.hex())
        print(f"🔐 New private key generated and saved to {filename}")
    else:
        with open(filename, "r") as f:
            key = f.read().strip()
        acct = eth_account.Account.from_key(key)

    eth_addr = acct.address
    w3 = Web3()
    message = encode_defunct(challenge)

    # Sign the message using the account's private key
    signed_message = acct.sign_message(message)

    # Verify that the signature matches the address
    assert eth_account.Account.recover_message(message, signature=signed_message.signature.hex()) == eth_addr, f"Failed to sign message properly"

    # return signed_message, account associated with the private key
    return signed_message, eth_addr


if __name__ == "__main__":
    for i in range(4):
        challenge = os.urandom(64)
        sig, addr = sign_message(challenge=challenge)
        print(addr)

