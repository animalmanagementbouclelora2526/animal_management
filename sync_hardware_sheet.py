import gspread
from google.oauth2.service_account import Credentials
import requests
import json
import os

# =====================================================================
# 🛠️ CONFIGURATION
# =====================================================================

# 1. API endpoint of the website (change to local or live production URL)
WEB_URL = "https://livestockmanagment.vercel.app"  # or "http://127.0.0.1:5000"

# 2. Breeder login credentials to authenticate session
BREEDER_USERNAME = "bbeddad"
BREEDER_PASSWORD = "BEDDAD2"

# 3. Google Sheet Key where the hardware device inserts tracking data
# (This key corresponds to the client's shared Animal_management sheet)
HARDWARE_SHEET_ID = "1YkSZ26-iTuKCWEz4d_ZSm0qaufIhka5WpWp9cI1tVoo" 

# 4. Google Service Account JSON Key file (from the client)
# Place the client's credentials JSON key file in the same directory and name it 'credentials.json'
CREDENTIALS_FILE = "credentials.json"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def main():
    print("[1/4] Connecting to the Client's Hardware Google Sheet...")
    if not os.path.exists(CREDENTIALS_FILE):
        print(f"Error: '{CREDENTIALS_FILE}' not found.")
        print("Please place the service account JSON key file in the same folder and name it 'credentials.json'.")
        return

    try:
        # Authenticate with Google Sheets API
        creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
        client = gspread.authorize(creds)
        
        # Open using the unique spreadsheet ID
        spreadsheet = client.open_by_key(HARDWARE_SHEET_ID)
        
        # Select the 'Animal' worksheet tab
        worksheet = spreadsheet.worksheet("Animal")
        records = worksheet.get_all_records()
        print(f"Successfully read {len(records)} records from client's 'Animal' worksheet.")
    except Exception as e:
        print(f"Error connecting to Google Sheet: {e}")
        print("Please check that the Google Sheet name is correct and shared with the service account email.")
        return

    # Map the rows from Google Sheet to the format required by the website API
    print("[2/4] Mapping hardware data to website format...")
    mapped_animals = []
    for idx, row in enumerate(records):
        try:
            # Map columns to correct API names. Edit the keys below to match the client's spreadsheet headers:
            mac = str(row.get("MAC", row.get("MAC Address", row.get("RFID", "")))).strip()
            category = str(row.get("Category", "Bovin")).strip()
            gender = str(row.get("Gender", "Male")).strip()
            birth_date = str(row.get("Birth_date", row.get("Birth Date", "2020-01-01"))).strip()
            vaccines = str(row.get("Vaccines", "None")).strip()
            latitude = str(row.get("Latitude", "0.0")).strip()
            longitude = str(row.get("Longitude", "0.0")).strip()
            battery = str(row.get("Battery_status", row.get("Battery", "100"))).strip()
            alerts = str(row.get("Aler_Hist", row.get("Alerts", "None"))).strip()
            status = str(row.get("Animal_status", row.get("Status", "ACTIVE"))).strip()

            if not mac:
                print(f"Skipping row {idx+2}: Missing MAC Address/RFID")
                continue

            mapped_animals.append({
                "mac": mac,
                "category": category,
                "gender": gender,
                "Birth_date": birth_date,
                "vaccines": vaccines,
                "Latitude": latitude,
                "Longitude": longitude,
                "Battery_status": battery,
                "Aler_Hist": alerts,
                "Animal_status": status
            })
        except Exception as e:
            print(f"Skipping row {idx+2} due to mapping error: {e}")

    if not mapped_animals:
        print("No valid animal records found to synchronize.")
        return

    print(f"Mapped {len(mapped_animals)} animals successfully.")

    # Authenticate and login to the website as the breeder
    print("[3/4] Logging into the website...")
    session = requests.Session()
    try:
        login_resp = session.post(f"{WEB_URL}/login", data={
            "username": BREEDER_USERNAME,
            "password": BREEDER_PASSWORD
        })
        if login_resp.status_code != 200 or "Login" in login_resp.text:
            print("Authentication failed. Please verify the breeder username/password.")
            return
        print("Logged in successfully!")
    except Exception as e:
        print(f"Connection to website failed: {e}")
        return

    # Send data to /sync_animals endpoint
    print("[4/4] Synchronizing animal records to database...")
    payload = {"animals": mapped_animals}
    try:
        headers = {"Content-Type": "application/json"}
        sync_resp = session.post(f"{WEB_URL}/sync_animals", json=payload, headers=headers)
        if sync_resp.status_code == 200:
            print("Synchronization completed successfully!")
            print(json.dumps(sync_resp.json(), indent=2))
        else:
            print(f"Synchronization failed (HTTP {sync_resp.status_code}):")
            print(sync_resp.text)
    except Exception as e:
        print(f"Request failed: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    main()
