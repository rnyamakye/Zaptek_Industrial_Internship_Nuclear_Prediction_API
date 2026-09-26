import sys
import os

# Append current path to sys.path so we can import app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app
from app.db.database import Base, engine

client = TestClient(app)

def run_tests():
    # Ensure tables are created
    Base.metadata.create_all(bind=engine)

    print("1. Registering a new user...")
    resp = client.post("/auth/register", json={
        "name": "Test User",
        "email": "test@example.com",
        "password": "securepassword"
    })
    
    if resp.status_code == 409:
        print("User already exists, proceeding to login...")
    else:
        if resp.status_code != 201:
            print(f"Failed to register: {resp.text}")
            return
        print("User registered successfully.")

    print("\n2. Logging in...")
    resp = client.post("/auth/login", data={
        "username": "test@example.com",
        "password": "securepassword",
        "grant_type": "password"
    })
    if resp.status_code != 200:
        print(f"Failed to log in: {resp.text}")
        return
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"Logged in successfully. Token: {token[:20]}...")

    print("\n3. Testing /auth/me...")
    resp = client.get("/auth/me", headers=headers)
    if resp.status_code != 200:
        print("Failed to get /auth/me")
        return
    print(f"Current user: {resp.json()['name']} ({resp.json()['email']})")

    print("\n4. Making a prediction...")
    payload = {
        "enrichment_percent": 4.5,
        "fuel_density": 10.2,
        "moderator_density": 0.98,
    }
    resp = client.post("/predictions", json=payload, headers=headers)
    if resp.status_code != 201:
        print(f"Failed to predict: {resp.text}")
        return
    prediction = resp.json()
    print(f"Prediction successful! k_eff: {prediction['k_eff']}, status: {prediction['reactor_status']}")
    
    print("\n5. Fetching user's predictions...")
    resp = client.get("/predictions", headers=headers)
    if resp.status_code != 200:
        print(f"Failed to get predictions: {resp.text}")
        return
    predictions = resp.json()
    print(f"User has {len(predictions)} prediction(s).")
    
    print("\nAll tests passed successfully!")

if __name__ == "__main__":
    run_tests()
