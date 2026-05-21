import requests
import json

# Configuration
BASE_URL = "http://localhost:5000"  # Change if your Flask app runs elsewhere
LOGIN_URL = f"{BASE_URL}/login"
SYNC_URL = f"{BASE_URL}/sync_animals"

# Test credentials (use your admin or eleveur credentials)
TEST_USER = {
    "username": "wtaousser",
    "password": "24681357"
}

# Sample animal data to sync
TEST_ANIMALS = {
    "animals": [
        {
            "rfid_tag": "RFID1011",
            "category": "Bovin",
            "gender": "Male",
            "birth_date": "2020-06-15",
            "vaccines": "Vaccine C, Vaccine E"
        },
        {
            "rfid_tag": "RFID1012",
            "category": "Ovin",
            "gender": "Female",
            "birth_date": "2025-01-10",
            "vaccines": "Vaccine E"
        }
    ]
}

def simulate_sync():
    # Step 1: Login to get a session
    with requests.Session() as session:
        login_response = session.post(
            LOGIN_URL,
            data={"username": TEST_USER["username"], "password": TEST_USER["password"]}
        )
        
        if login_response.status_code != 200:
            print(f"Login failed: {login_response.text}")
            return

        # Step 2: Send sync request
        sync_response = session.post(
            SYNC_URL,
            json=TEST_ANIMALS,
            headers={"Content-Type": "application/json"}
        )

        # Step 3: Print results
        if sync_response.status_code == 200:
            print("Sync successful!")
            print(json.dumps(sync_response.json(), indent=2))
        else:
            print(f"Sync failed: {sync_response.text}")

if __name__ == "__main__":
    simulate_sync()