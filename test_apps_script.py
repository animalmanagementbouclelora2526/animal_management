import requests
import sys
import random
import time

def send_request(web_app_url, params, label):
    print(f"\n--- Sending request for: {label} ---")
    print("Parameters:")
    for k, v in params.items():
        print(f"  - {k}: {v}")
    try:
        response = requests.get(web_app_url, params=params, timeout=15)
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def run_test_suite(web_app_url):
    print("========================================")
    print("🧪 Interactive Google Apps Script Test Suite")
    print("========================================")
    print("Select a scenario to test:")
    print("1) Test Scenario 1: New Alert Case (ALERTE)")
    print("2) Test Scenario 2: Deceased Case (MORT)")
    print("3) Test Scenario 3: Animal Sale / Transfer (VENDU)")
    print("4) Test Scenario 4: New Animal Registration")
    print("========================================")
    
    choice = input("Enter option (1-4): ").strip()
    
    test_mac = f"AA:BB:CC:DD:EE:{random.randint(10, 99)}"
    
    if choice == "1":
        # New Alert
        params = {
            "ID": "100",
            "MAC": test_mac,
            "Category": "Ovin",
            "Gender": "Female",
            "BirthDate": "2024-01-15",
            "Vaccines": "None",
            "Lat": "35.1982",
            "Lon": "-0.6278",
            "Battery": "15",
            "Alert": f"ALERTE: Battery critical {random.randint(1000, 9999)}",
            "Status": "ALERTE",
            "FarmerID": "3",  # hmly (sidoa065@gmail.com)
            "LastSync": str(time.time())
        }
        success = send_request(web_app_url, params, "Scenario 1: Active Alert")
        if success:
            print("\n[SUCCESS] Check inbox. Both breeder (sidoa065@gmail.com) and admin (sidoa065@gmail.com) should receive the alert email.")

    elif choice == "2":
        # Deceased: First sync as ACTIVE, then sync as MORT
        params_active = {
            "ID": "101",
            "MAC": test_mac,
            "Category": "Bovin",
            "Gender": "Male",
            "BirthDate": "2022-03-20",
            "Vaccines": "Vaccine A",
            "Lat": "35.2001",
            "Lon": "-0.6300",
            "Battery": "98",
            "Alert": "None",
            "Status": "ACTIVE",
            "FarmerID": "3",
            "LastSync": str(time.time())
        }
        print("Registering animal as ACTIVE first...")
        if send_request(web_app_url, params_active, "Deceased Step 1: Active Animal"):
            time.sleep(2)
            params_mort = params_active.copy()
            params_mort["Status"] = "MORT"
            success = send_request(web_app_url, params_mort, "Deceased Step 2: MORT Status Change")
            if success:
                print("\n[SUCCESS] Check inbox. Both breeder (sidoa065@gmail.com) and admin (sidoa065@gmail.com) should receive the Deceased (MORT) email.")

    elif choice == "3":
        # Ownership Transfer: First sync under FarmerID 3 (hmly), then under FarmerID 2 (gtest)
        params_breeder1 = {
            "ID": "102",
            "MAC": test_mac,
            "Category": "Bovin",
            "Gender": "Female",
            "BirthDate": "2023-11-05",
            "Vaccines": "Vaccine B",
            "Lat": "35.2010",
            "Lon": "-0.6290",
            "Battery": "85",
            "Alert": "None",
            "Status": "ACTIVE",
            "FarmerID": "3", # Initial owner: hmly (sidoa065@gmail.com)
            "LastSync": str(time.time())
        }
        print("Registering animal under Breeder 1 (FarmerID 3)...")
        if send_request(web_app_url, params_breeder1, "Transfer Step 1: Breeder 1 Registration"):
            time.sleep(2)
            params_breeder2 = params_breeder1.copy()
            params_breeder2["FarmerID"] = "2" # New owner: gtest (gg@gmail.com)
            success = send_request(web_app_url, params_breeder2, "Transfer Step 2: Breeder 2 Registration (Sale)")
            if success:
                print("\n[SUCCESS] Check inbox. Only the Admin (sidoa065@gmail.com) should receive this Sale / Duplicate Registration warning email.")

    elif choice == "4":
        # New animal registration
        params = {
            "ID": "103",
            "MAC": test_mac,
            "Category": "Caprin",
            "Gender": "Male",
            "BirthDate": "2025-02-10",
            "Vaccines": "Vaccine C",
            "Lat": "35.1950",
            "Lon": "-0.6250",
            "Battery": "100",
            "Alert": "None",
            "Status": "ACTIVE",
            "FarmerID": "3",
            "LastSync": str(time.time())
        }
        success = send_request(web_app_url, params, "Scenario 4: New Animal Registration")
        if success:
            print("\n[SUCCESS] Check inbox. Both breeder (sidoa065@gmail.com) and admin (sidoa065@gmail.com) should receive the 'New Animal Registered' email.")

    else:
        print("Invalid option selected.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_apps_script.py <YOUR_APPS_SCRIPT_WEB_APP_URL>")
        print("Example: python test_apps_script.py https://script.google.com/macros/s/AKfycbyg.../exec")
        sys.exit(1)
        
    url = sys.argv[1]
    run_test_suite(url)
