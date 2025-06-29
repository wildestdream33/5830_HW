import json
import requests

# Pinata JWT (keep this private)
PINATA_JWT = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySW5mb3JtYXRpb24iOnsiaWQiOiJiZmY5MmQ5NC0xZjU2LTRhMjQtOGQwZC0wNzk4MDY2MTkwYjQiLCJlbWFpbCI6InJ1b3hpd2FuZzlAZ21haWwuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsInBpbl9wb2xpY3kiOnsicmVnaW9ucyI6W3siZGVzaXJlZFJlcGxpY2F0aW9uQ291bnQiOjEsImlkIjoiRlJBMSJ9LHsiZGVzaXJlZFJlcGxpY2F0aW9uQ291bnQiOjEsImlkIjoiTllDMSJ9XSwidmVyc2lvbiI6MX0sIm1mYV9lbmFibGVkIjpmYWxzZSwic3RhdHVzIjoiQUNUSVZFIn0sImF1dGhlbnRpY2F0aW9uVHlwZSI6InNjb3BlZEtleSIsInNjb3BlZEtleUtleSI6IjBlYTBkODdhMDcyMDE0MDlmYjQ5Iiwic2NvcGVkS2V5U2VjcmV0IjoiMTRhN2RhMGI3NjlkNTQyOWY4ZGI4YWJiOTYwYzFlZjI2MGViN2FmMDcwYmMzY2NjNTNiZTlhMTk4MjY5NzdkMCIsImV4cCI6MTc4Mjc1NDU1Nn0.K3T-WcVTsEccCy1AqeB85kSUy_Wt7IiiMAi4GPy4VJ4"

def pin_to_ipfs(json_data):
    """
    Upload a Python dictionary as JSON to IPFS via Pinata and return the CID.
    """
    url = "https://api.pinata.cloud/pinning/pinJSONToIPFS"
    headers = {
        "Authorization": PINATA_JWT,
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(url, headers=headers, json=json_data)
        response.raise_for_status()
        ipfs_hash = response.json()["IpfsHash"]
        return ipfs_hash
    except Exception as e:
        print("pin_to_ipfs ERROR:", e)
        return None

def get_from_ipfs(cid):
    """
    Fetch a JSON object from IPFS using the given CID and return it as a Python dict.
    """
    url = f"https://gateway.pinata.cloud/ipfs/{cid}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print("get_from_ipfs ERROR:", e)
        return None






