import json
import os
import gspread
from google.oauth2.service_account import Credentials
from werkzeug.security import generate_password_hash

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Unique ID of your Website Database Spreadsheet (Spreadsheet 2)
DATABASE_SHEET_ID = "1YkSZ26-iTuKCWEz4d_ZSm0qaufIhka5WpWp9cI1tVoo"

def main():
    print("[1/3] Connecting to the Website Google Sheet Database...")
    if not os.path.exists("credentials.json"):
        print("Error: credentials.json not found.")
        return

    try:
        info = json.load(open("credentials.json"))
        creds = Credentials.from_service_account_info(info, scopes=SCOPES)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(DATABASE_SHEET_ID)
        print(f"Connected successfully to database spreadsheet ID: {DATABASE_SHEET_ID}")
    except Exception as e:
        print(f"Error connecting: {e}")
        return

    worksheets_def = ["Users", "Registration_requests", "Animal", "positions_history", "alerts_history"]

    print("\n[2/3] Clearing all worksheets data (keeping headers)...")
    for name in worksheets_def:
        try:
            ws = spreadsheet.worksheet(name)
            # Resize worksheet to 1 row to clear all data rows
            ws.resize(rows=1)
            # Resize back to 100 rows to leave space for future entries
            ws.resize(rows=100)
            print(f"  - Cleared '{name}' worksheet successfully.")
        except Exception as e:
            print(f"  - Error clearing '{name}': {e}")

    print("\n[3/3] Creating default Administrator account...")
    try:
        users_sheet = spreadsheet.worksheet("Users")
        admin_password = "07No1986/"
        hashed_password = generate_password_hash(admin_password)
        
        # Row layout: Eleveur_ID, Username, Password, Role, Email
        users_sheet.append_row([
            1, 
            "HADJIAhmed", 
            hashed_password, 
            "admin", 
            "ahmed.hadji2219@gmail.com"
        ])
        print("SUCCESS: Default admin account 'HADJIAhmed' created!")
        print("Credentials:")
        print("  Username: HADJIAhmed")
        print("  Password: 07No1986/")
    except Exception as e:
        print(f"Error creating admin: {e}")

if __name__ == "__main__":
    main()
