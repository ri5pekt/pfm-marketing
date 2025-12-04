"""Test the login endpoint"""
import requests
import json

url = "http://localhost:8000/api/auth/login"
data = {
    "email": "admin@example.com",
    "password": "admin123"
}

try:
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    if response.status_code == 200:
        token_data = response.json()
        print(f"Token: {token_data.get('access_token', 'N/A')[:50]}...")
except Exception as e:
    print(f"Error: {e}")

