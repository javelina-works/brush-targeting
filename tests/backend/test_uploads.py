import pytest
import requests
import json
import time
from tests.test_configs import BASE_URL


# ✅ Helper function to make API calls
def make_request(method, endpoint, data=None):
    url = f"{BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    print(data)
    print(json.dumps(data))
    
    if method == "GET":
        response = requests.get(url, params=data)
    elif method == "POST":
        response = requests.post(url, headers=headers, json=data)
    elif method == "PUT":
        response = requests.put(url, headers=headers, json=data)
    elif method == "DELETE":
        response = requests.delete(url)
    else:
        raise ValueError("Invalid method")
    
    return response