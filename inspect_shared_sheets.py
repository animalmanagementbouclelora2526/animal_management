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
        for s in sheets:
            print(f"\nSpreadsheet: '{s.title}' (ID: {s.id})")
            print("Worksheets:")
            for ws in s.worksheets():
                try:
                    headers = ws.row_values(1)
                    print(f"  - '{ws.title}' (Headers: {headers})")
                except Exception as e:
                    print(f"  - '{ws.title}' (Error: {e})")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
