import requests
import json
import time

BASE_URL = "http://127.0.0.1:5000"
TEST_MAC = "00:11:22:33:44:55"

def test_workflow():
    print("[RUN] Starting real-email trigger workflow against localhost...")
    session = requests.Session()
    
    # ----------------------------------------------------
    # Step 1: Login as Breeder 'ttest' (Farmer_ID = 3)
    # ----------------------------------------------------
    print("\n1. Logging in as breeder 'ttest'...")
    login_resp = session.post(f"{BASE_URL}/login", data={
        "username": "ttest",
        "password": "zk,w*mdIM+"
    })
    if login_resp.status_code != 200 or "Login" in login_resp.text and "Dashboard" not in login_resp.text:
        print("[FAIL] Login failed. Please ensure the local Flask server is running.")
        return
    print("[OK] Logged in successfully!")
    
    # ----------------------------------------------------
    # Step-2: Register/Sync animal as ACTIVE
    # ----------------------------------------------------
    print(f"\n2. Registering animal {TEST_MAC} as ACTIVE...")
    sync_payload = {
        "animals": [
            {
                "mac": TEST_MAC,
                "category": "Bovin",
                "gender": "Female",
                "Birth_date": "2022-01-01",
                "vaccines": "Vaccine A",
                "Latitude": "35.1982",
                "Longitude": "-0.6278",
                "Battery_status": "95",
                "Aler_Hist": "None",
                "Animal_status": "ACTIVE"
            }
        ]
    }
    sync_resp = session.post(f"{BASE_URL}/sync_animals", json=sync_payload)
    print(f"Status Code: {sync_resp.status_code}, Response: {sync_resp.json()}")

    # ----------------------------------------------------
    # Step 3: Sync same animal as MORT (Deceased)
    # ----------------------------------------------------
    print(f"\n3. Syncing animal {TEST_MAC} with status MORT (Deceased)...")
    sync_payload["animals"][0]["Animal_status"] = "MORT"
    sync_resp = session.post(f"{BASE_URL}/sync_animals", json=sync_payload)
    print(f"Status Code: {sync_resp.status_code}, Response: {sync_resp.json()}")
    print("[INFO] Deceased (MORT) email notification should now be triggered!")
    
    # Wait a bit before proceeding
    time.sleep(2)
    session.close()
    
    # ----------------------------------------------------
    # Step 4: Login as Breeder 'bahmed' (Farmer_ID = 4)
    # ----------------------------------------------------
    session2 = requests.Session()
    print("\n4. Logging in as breeder 'bahmed'...")
    login_resp = session2.post(f"{BASE_URL}/login", data={
        "username": "bahmed",
        "password": "7L\"bH+i(\"C"
    })
    if login_resp.status_code != 200:
        print("[FAIL] Login failed for bahmed.")
        return
    print("[OK] Logged in successfully as 'bahmed'!")

    # ----------------------------------------------------
    # Step 5: Sync the same animal (will trigger VENDU / Sale)
    # ----------------------------------------------------
    print(f"\n5. Syncing animal {TEST_MAC} under 'bahmed' (Triggering VENDU / Sale)...")
    # Change status back to ACTIVE under new breeder (representing the purchase)
    sync_payload["animals"][0]["Animal_status"] = "ACTIVE"
    sync_payload["animals"][0]["Battery_status"] = "90"
    
    sync_resp = session2.post(f"{BASE_URL}/sync_animals", json=sync_payload)
    print(f"Status Code: {sync_resp.status_code}, Response: {sync_resp.json()}")
    print("[INFO] Sale (VENDU) email notification should now be triggered!")
    
    session2.close()
    print("\n[INFO] Done! Check your inbox at sidoa065@gmail.com for the notifications.")

if __name__ == "__main__":
    test_workflow()
