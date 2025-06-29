import requests
import json
import base64

INFURA_PROJECT_ID = "d9ca8eed551d4ccda325b963d8d71777"
INFURA_PROJECT_SECRET = "tRPgr9T1imK22lFxofOXrTeYVrx5WHPRZZO2bP3aer0kYuhZDchskw"
INFURA_URL = "https://ipfs.infura.io:5001"

# Properly encoded Basic Auth header
auth = (INFURA_PROJECT_ID + ':' + INFURA_PROJECT_SECRET).encode('utf-8')
headers = {
    "Authorization": "Basic " + base64.b64encode(auth).decode('utf-8')
}

def pin_to_ipfs(data):
    assert isinstance(data, dict), f"Error pin_to_ipfs expects a dictionary"
    json_data = json.dumps(data)
    files = {'file': json_data}

    response = requests.post(f"{INFURA_URL}/api/v0/add", files=files, headers=headers)
    response.raise_for_status()  # Raise error for HTTP issues
    cid = response.json()["Hash"]
    return cid

def get_from_ipfs(cid):
    assert isinstance(cid, str), f"get_from_ipfs accepts a cid in the form of a string"

    params = {'arg': cid}
    response = requests.post(f"{INFURA_URL}/api/v0/cat", params=params, headers=headers)
    response.raise_for_status()
    data = json.loads(response.text)

    assert isinstance(data, dict), f"get_from_ipfs should return a dict"
    return data





