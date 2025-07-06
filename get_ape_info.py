from web3 import Web3
from web3.providers.rpc import HTTPProvider
import requests
from requests.auth import HTTPBasicAuth
import json

# Bored Ape Yacht Club contract address
bayc_address = "0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D"
contract_address = Web3.to_checksum_address(bayc_address)

# Load contract ABI
with open('ape_abi.json', 'r') as f:
    abi = json.load(f)

############################
# Connect to Ethereum node via Infura
project_id = "e03b544561e94e90a79c8867bdc0c35e"
project_secret = "tQgwk1K2Hupu4mXutm6QDx6mbGZKaUupknsj2QwbTMTZ3xF4IUw5zA"
url = f"https://mainnet.infura.io/v3/{project_id}"

session = requests.Session()
session.auth = HTTPBasicAuth(project_id, project_secret)

provider = HTTPProvider(endpoint_uri=url, session=session)
web3 = Web3(provider)

# Check connection
assert web3.is_connected(), f"❌ Failed to connect to provider at {url}"
print("✅ Connected to Ethereum Mainnet")

# Instantiate contract
contract = web3.eth.contract(address=contract_address, abi=abi)


def get_ape_info(ape_id):
    assert isinstance(ape_id, int), f"{ape_id} is not an int"
    assert 0 <= ape_id, f"{ape_id} must be at least 0"
    assert 9999 >= ape_id, f"{ape_id} must be less than 10,000"

    data = {'owner': "", 'image': "", 'eyes': ""}

    try:
        # Get owner
        owner = contract.functions.ownerOf(ape_id).call()
        data['owner'] = owner

        # Get token URI and resolve IPFS
        token_uri = contract.functions.tokenURI(ape_id).call()
        if token_uri.startswith("ipfs://"):
            ipfs_hash = token_uri.replace("ipfs://", "")
            metadata_url = f"https://ipfs.io/ipfs/{ipfs_hash}"
        else:
            metadata_url = token_uri

        # Fetch metadata JSON
        response = requests.get(metadata_url)
        metadata = response.json()

        # Get image
        data['image'] = metadata.get("image", "")

        # Get "Eyes" attribute
        for attribute in metadata.get("attributes", []):
            if attribute.get("trait_type") == "Eyes":
                data["eyes"] = attribute.get("value", "")
                break

    except Exception as e:
        print(f"⚠️ Error retrieving data for Ape {ape_id}: {e}")

    assert isinstance(data, dict), f'get_ape_info({ape_id}) should return a dict'
    assert all(key in data for key in ['owner', 'image', 'eyes']), \
        "Return value must include 'owner', 'image', and 'eyes'"
    return data

