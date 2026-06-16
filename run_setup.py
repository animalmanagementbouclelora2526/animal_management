import json
import os
import gspread
from google.oauth2.service_account import Credentials
from werkzeug.security import generate_password_hash

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def run():
    creds_path = "animaltracker-499320-0c2c76b1a2ff.json"
    if not os.path.exists(creds_path):
        print(f"Error: Credentials file '{creds_path}' not found in the root directory.")
        return
        
    print(f"Reading credentials from {creds_path}...")
    with open(creds_path, 'r') as f:
        creds_data = json.load(f)
        
    service_account_email = creds_data.get("client_email")
    print(f"Service Account Email: {service_account_email}")
    
    # Write .env file first so it is ready
    env_content = f"GOOGLE_CREDS={json.dumps(creds_data)}\n"
    with open(".env", "w") as env_file:
        env_file.write(env_content)
    print("Created local '.env' file successfully.")
    
    try:
        creds = Credentials.from_service_account_info(creds_data, scopes=SCOPES)
        client = gspread.authorize(creds)
        print("Authorized with Google Sheets APIs.")
    except Exception as e:
        print(f"Authorization failed: {e}")
        return
        
    spreadsheet_name = "Animal_management"
    spreadsheet = None
    
    try:
        spreadsheet = client.open(spreadsheet_name)
        print(f"Opened existing Google Sheet '{spreadsheet_name}'.")
    except gspread.SpreadsheetNotFound:
        print(f"\n========================================================")
        print(f"ACTION REQUIRED: Google Sheet '{spreadsheet_name}' not found.")
        print(f"Service Accounts cannot create files directly due to Drive storage quotas.")
        print(f"Please perform the following steps:")
        print(f"1. Go to Google Sheets (https://sheets.google.com) and create a sheet named: {spreadsheet_name}")
        print(f"2. Click 'Share' at the top-right and add this email as an 'Editor':")
        print(f"   {service_account_email}")
        print(f"3. Run this script again: venv\\Scripts\\python run_setup.py")
        print(f"========================================================\n")
        return
            
    # Set up worksheets and headers
    worksheets_def = {
        "Users": ["Eleveur_ID", "Username", "Password", "Role", "Email"],
        "Registration_requests": ["ID", "Name", "First_name", "Email", "Card_number", "Status", "Request_date"],
        "Animal": ["ID", "MAC", "Category", "Gender", "Birth_date", "Vaccines", "Latitude", "Longitude", "Battery_status", "Aler_Hist", "Animal_status", "Farmer_ID", "Last_Sync"],
        "positions_history": ["ID", "MAC", "Latitude", "Longitude", "Date", "Animal_ID"],
        "alerts_history": ["ID", "MAC", "Alert", "Latitude", "Longitude", "Date"]
    }
    
    for ws_name, headers in worksheets_def.items():
        try:
            worksheet = spreadsheet.worksheet(ws_name)
            print(f"Worksheet '{ws_name}' already exists.")
            existing_headers = worksheet.row_values(1)
            if not existing_headers:
                worksheet.append_row(headers)
                print(f"Added headers to '{ws_name}'.")
            else:
                # Migrate existing headers if necessary
                if ws_name == "Registration_requests" and len(existing_headers) >= 7 and existing_headers[6] == "Date":
                    worksheet.update_cell(1, 7, "Request_date")
                    print("Updated Registration_requests header 'Date' to 'Request_date'")
                if ws_name == "alerts_history" and len(existing_headers) >= 3 and existing_headers[2] == "Aler_Hist":
                    worksheet.update_cell(1, 3, "Alert")
                    print("Updated alerts_history header 'Aler_Hist' to 'Alert'")
                if ws_name == "positions_history" and len(existing_headers) >= 5 and "Animal_ID" not in existing_headers:
                    worksheet.update_cell(1, 6, "Animal_ID")
                    print("Updated positions_history header, added 'Animal_ID'")
        except gspread.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title=ws_name, rows=100, cols=len(headers) + 2)
            worksheet.append_row(headers)
            print(f"Created worksheet '{ws_name}' with headers.")
            
    # Populate Default Admin User
    users_sheet = spreadsheet.worksheet("Users")
    users = users_sheet.get_all_records()
    admin_exists = any(u.get("Username") == "HADJIAhmed" for u in users)
    
    if not admin_exists:
        admin_password = "07No1986/"
        hashed_password = generate_password_hash(admin_password)
        users_sheet.append_row([
            1, 
            "HADJIAhmed", 
            hashed_password, 
            "admin", 
            "ahmed.hadji2219@gmail.com"
        ])
        print("Default admin user 'HADJIAhmed' created.")
    else:
        print("Default admin user 'HADJIAhmed' already exists.")
        
    print("Setup completed successfully!")

if __name__ == "__main__":
    run()
