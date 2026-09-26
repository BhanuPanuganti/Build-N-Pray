import os
import requests
from pymongo import MongoClient

mongo_uri = "mongodb+srv://vishnudatta2004_db_user:TWtpNynGDI9dHwco@bnb.wfnygwm.mongodb.net/?appName=bnb"
client = MongoClient(mongo_uri)
db = client["bnb_interview"]

interview = db.interviews.find_one()
if not interview:
    print("No interview found")
else:
    token = interview["token"]
    print(f"Found token: {token}")
    
    headers = {"Content-Type": "application/json"}
    
    reg_resp = requests.post("http://127.0.0.1:8000/api/auth/register", json={
        "name": "Test Candidate",
        "email": "testcand@example.com",
        "password": "password123",
        "role": "candidate",
        "admin_access_code": ""
    })
    if reg_resp.status_code in (200, 201):
        cand_token = reg_resp.json()["token"]
    elif reg_resp.status_code == 409:
        login_resp = requests.post("http://127.0.0.1:8000/api/auth/login", json={
            "email": "testcand@example.com",
            "password": "password123"
        })
        cand_token = login_resp.json()["token"]
    else:
        print(f"Reg failed: {reg_resp.text}")
        cand_token = None
        
    if cand_token:
        print("Joining interview...")
        resp = requests.post(f"http://127.0.0.1:8000/api/interviews/{token}/sessions", json={
            "resume": "This is a dummy resume with more than 10 characters."
        }, headers={"Authorization": f"Bearer {cand_token}"})
        print(f"Status: {resp.status_code}")
        print(f"Body: {resp.text}")
