import requests
import json

url = "http://localhost:5000/api/analyze"
payload = {"ticker": "AAPL"}
headers = {"Content-Type": "application/json"}

try:
    response = requests.post(url, data=json.dumps(payload), headers=headers, timeout=30)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
