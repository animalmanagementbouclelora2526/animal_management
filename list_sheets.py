import gspread
from google.oauth2.service_account import Credentials
import json
import os

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def main():
    if not os.path.exists("credentials.json"):
        print("Error: credentials.json not found.")
        return

    try:
        info = json.load(open("credentials.json"))
        creds = Credentials.from_service_account_info(info, scopes=SCOPES)
        client = gspread.authorize(creds)
        
        sheets = client.openall()
        print("\nSpreadsheets shared with your Service Account:")
        if not sheets:
            print("No spreadsheets found! Please make sure you have shared the client's sheet with:")
            print(f"👉 {info['client_email']}")
        else:
            for s in sheets:
                print(f"- Name: '{s.title}' (ID: {s.id})")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
