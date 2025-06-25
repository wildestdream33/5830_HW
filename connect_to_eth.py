import json
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
from web3.providers.rpc import HTTPProvider

'''
If you use one of the suggested infrastructure providers, the url will be of the form
now_url  = f"https://eth.nownodes.io/{now_token}"
alchemy_url = f"https://eth-mainnet.alchemyapi.io/v2/{alchemy_token}"
infura_url = f"https://mainnet.infura.io/v3/{infura_token}"
'''

def connect_to_eth():
	url = "https://mainnet.infura.io/v3/d9ca8eed551d4ccda325b963d8d71777"  # Your Infura Project ID
	w3 = Web3(HTTPProvider(url))
	assert w3.is_connected(), f"Failed to connect to provider at {url}"
	print("✅ Connected to Ethereum Mainnet")
	return w3


def connect_with_middleware(contract_json):
	with open(contract_json, "r") as f:
		d = json.load(f)
		d = d['bsc']
		address = d['address']
		abi = d['abi']

	# Connect to BNB testnet
	w3 = Web3(HTTPProvider("https://data-seed-prebsc-1-s1.binance.org:8545"))
	assert w3.is_connected(), "Failed to connect to BNB testnet"

	# Inject middleware required for BNB (Proof-of-Authority consensus)
	w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

	# Create contract object
	contract = w3.eth.contract(address=address, abi=abi)

	return w3, contract






if __name__ == "__main__":
	connect_to_eth()

	