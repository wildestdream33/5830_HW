import json
import requests
from base64 import b64encode

# Your Infura credentials
INFURA_PROJECT_ID = "d9ca8eed551d4ccda325b963d8d71777"
INFURA_PROJECT_SECRET = "tRPgr9T1imK22lFxofOXrTeYVrx5WHPRZZO2bP3aer0kYuhZDchskw"

# Prepare the authorization header
auth_str = f"{INFURA_PROJECT_ID}:{INFURA_PROJECT_SECRET}"
auth_bytes = auth_str.encode("utf-8")
auth_b64 = b64encode(auth_bytes).decode("utf-8")

headers = {
    "Authorization": f"Basic {auth_b64}"
}

def pin_to_ipfs(data):
    assert isinstance(data, dict), "pin_to_ipfs expects a dictionary"
    try:
        files = {
            'file': ('data.json', json.dumps(data))
        }
        res = requests.post(
            "https://ipfs.infura.io:5001/api/v0/add",
            headers=headers,
            files=files
        )
        res.raise_for_status()
        return res.json()["Hash"]
    except Exception as e:
        print("pin_to_ipfs ERROR:", e)
        return None

def get_from_ipfs(cid, content_type="json"):
    assert isinstance(cid, str), "get_from_ipfs expects a CID string"
    try:
        res = requests.post(
            f"https://ipfs.infura.io:5001/api/v0/cat?arg={cid}",
            headers=headers
        )
        res.raise_for_status()
        if content_type == "json":
            return json.loads(res.text)
        return res.text
    except Exception as e:
        print("get_from_ipfs ERROR:", e)
        return None




