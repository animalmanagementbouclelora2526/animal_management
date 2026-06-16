import json
import os
import gspread
from google.oauth2.service_account import Credentials

SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

def run():
    if "GOOGLE_CREDS" not in os.environ:
        if os.path.exists(".env"):
            with open(".env", "r") as f:
                for line in f:
                    if "=" in line and not line.strip().startswith("#"):
                        k, v = line.strip().split("=", 1)
                        if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                            v = v[1:-1]
                        os.environ[k] = v
                        
    info = json.loads(os.environ["GOOGLE_CREDS"])
    creds = Credentials.from_service_account_info(info, scopes=SCOPES)
    client = gspread.authorize(creds)
    spreadsheet = client.open("Animal_management")
    requests_sheet = spreadsheet.worksheet("Registration_requests")
    
    print("\nRegistration Requests:")
    for req in requests_sheet.get_all_records():
        if str(req.get('ID')) == '12':
            print(json.dumps(req, indent=2))
            return
    print("Request ID 12 not found!")

if __name__ == "__main__":
    run()
