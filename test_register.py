import requests
import json

url = "http://127.0.0.1:8000/api/auth/register"
headers = {
    "accept": "application/json",
    "Content-Type": "application/json"
}
data = {
    "email": "testuser999@gmail.com",
    "password": "Test12345",
    "role": "user"
}

try:
    response = requests.post(url, headers=headers, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Lỗi: {e}")
