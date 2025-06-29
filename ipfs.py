import requests
import json
from requests.auth import HTTPBasicAuth

INFURA_PROJECT_ID = "d9ca8eed551d4ccda325b963d8d71777"
INFURA_PROJECT_SECRET = "tRPgr9T1imkK221FxoFOXrTeYVrx5WHPRZZO2bP3aer0kYuhZDchskw"

auth = HTTPBasicAuth(INFURA_PROJECT_ID, INFURA_PROJECT_SECRET)

def pin_to_ipfs(data):
    assert isinstance(data, dict), f"Error pin_to_ipfs expects a dictionary"
    headers = {'Content-Type': 'application/json'}
    res = requests.post(
        "https://ipfs.infura.io:5001/api/v0/add",
        files={'file': json.dumps(data)},
        auth=auth
    )
    cid = res.json()['Hash']
    return cid

def get_from_ipfs(cid, content_type="json"):
    assert isinstance(cid, str), f"get_from_ipfs expects a CID string"
    res = requests.post(
        f"https://ipfs.infura.io:5001/api/v0/cat?arg={cid}",
        auth=auth
    )
    data = res.json()
    assert isinstance(data, dict), f"get_from_ipfs should return a dict"
    return data

