import requests

url = "http://localhost:8000/summarize"
payload = {
    "url": "https://example.com/terms",
    "text": "These are the terms and conditions. You must agree to all of them." * 10
}
try:
    response = requests.post(url, json=payload)
    print("STATUS:", response.status_code)
    print(response.json())
except Exception as e:
    print("ERROR:", e)
