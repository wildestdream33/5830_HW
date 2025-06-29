import requests
import json

# Infura IPFS credentials
INFURA_PROJECT_ID = "d9ca8eed551d4ccda325b963d8d71777"
INFURA_PROJECT_SECRET = "tRPgr9T1imkK221FxoFOXrTeYVrx5WHPRZZO2bP3aer0kYuhZDchskw"
INFURA_URL = "https://ipfs.infura.io:5001"

# Auth as a tuple for requests
auth = (INFURA_PROJECT_ID, INFURA_PROJECT_SECRET)

def pin_to_ipfs(data):
    assert isinstance(data, dict), "pin_to_ipfs expects a dictionary"
    
    # Convert dictionary to JSON string
    json_data = json.dumps(data)

    # Wrap as a file upload
    files = {
        'file': ('data.json', json_data)
    }

    try:
        response = requests.post(
            f"{INFURA_URL}/api/v0/add",
            files=files,
            auth=auth
        )
        response.raise_for_status()
        result = response.json()
        return result["Hash"]
    except Exception as e:
        print("pin_to_ipfs ERROR:", e)
        return None

def get_from_ipfs(cid, content_type="json"):
    assert isinstance(cid, str), "get_from_ipfs expects a string CID"

    try:
        response = requests.post(
            f"{INFURA_URL}/api/v0/cat?arg={cid}",
            auth=auth
        )
        response.raise_for_status()
        if content_type == "json":
            data = json.loads(response.text)
            assert isinstance(data, dict), "Returned data is not a dictionary"
            return data
        else:
            return response.text
    except Exception as e:
        print("get_from_ipfs ERROR:", e)
        return None


