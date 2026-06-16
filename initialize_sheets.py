import json
import sys
import os
import gspread
from google.oauth2.service_account import Credentials
from werkzeug.security import generate_password_hash

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def main():
    print("========================================")
    print("🟢 Google Sheets Initialization Utility")
    print("========================================\n")
    
    # 1. Ask for credentials path
    creds_path = input("Enter path to your downloaded service account JSON key file (e.g. credentials.json): ").strip()
    if not os.path.exists(creds_path):
        print(f"❌ Error: File '{creds_path}' not found.")
        sys.exit(1)
        
    try:
        with open(creds_path, 'r') as f:
            creds_data = json.load(f)
    except Exception as e:
        print(f"❌ Error reading JSON file: {e}")
        sys.exit(1)
        
    service_account_email = creds_data.get("client_email")
    print(f"\n🔑 Service Account Email: {service_account_email}")
    print("Please ensure this email is added as an 'Editor' on your Google Sheet if you already created it manually.\n")
    
    # 2. Authorize
    try:
        creds = Credentials.from_service_account_info(creds_data, scopes=SCOPES)
        client = gspread.authorize(creds)
        print("✅ Authorized successfully with Google APIs!")
    except Exception as e:
        print(f"❌ Google API authorization failed: {e}")
        sys.exit(1)
        
    # 3. Create or Open Spreadsheet
    spreadsheet_name = "Animal_management"
    spreadsheet = None
    
    print(f"Opening or creating spreadsheet '{spreadsheet_name}'...")
    try:
        spreadsheet = client.open(spreadsheet_name)
        print(f"✅ Found existing Google Sheet: '{spreadsheet_name}'")
    except gspread.SpreadsheetNotFound:
        print(f"ℹ️ Spreadsheet '{spreadsheet_name}' not found. Creating a new one...")
        try:
            spreadsheet = client.create(spreadsheet_name)
            print(f"✅ Created new Google Sheet: '{spreadsheet_name}'")
            
            # If created by service account, we should share it with the user
            user_email = input("Enter your personal email address to share this Google Sheet with: ").strip()
            if user_email:
                spreadsheet.share(user_email, perm_type='user', role='writer')
                print(f"📧 Shared the sheet with '{user_email}' as Editor. Check your Google Drive/Sheets!")
        except Exception as e:
            print(f"❌ Failed to create or share spreadsheet: {e}")
            sys.exit(1)
            
    # 4. Set up worksheets and headers
    worksheets_def = {
        "Users": ["Eleveur_ID", "Username", "Password", "Role", "Email"],
        "Registration_requests": ["ID", "Name", "First_name", "Email", "Card_number", "Status", "Date"],
        "Animal": ["ID", "MAC", "Category", "Gender", "Birth_date", "Vaccines", "Latitude", "Longitude", "Battery_status", "Aler_Hist", "Animal_status", "Farmer_ID", "Last_Sync"],
        "positions_history": ["ID", "MAC", "Latitude", "Longitude", "Date"],
        "alerts_history": ["ID", "MAC", "Aler_Hist", "Latitude", "Longitude", "Date"]
    }
    
    for ws_name, headers in worksheets_def.items():
        try:
            worksheet = spreadsheet.worksheet(ws_name)
            print(f"🔍 Worksheet '{ws_name}' already exists.")
            # Verify headers
            existing_headers = worksheet.row_values(1)
            if not existing_headers:
                worksheet.append_row(headers)
                print(f"   ℹ️ Added headers to '{ws_name}': {headers}")
        except gspread.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title=ws_name, rows=100, cols=len(headers) + 2)
            worksheet.append_row(headers)
            print(f"➕ Created worksheet '{ws_name}' with headers: {headers}")
            
    # 5. Populate Default Admin User
    users_sheet = spreadsheet.worksheet("Users")
    users = users_sheet.get_all_records()
    admin_exists = any(u.get("Username") == "HADJIAhmed" for u in users)
    
    if not admin_exists:
        print("👤 Creating default administrator account...")
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
        print("✅ Admin account 'HADJIAhmed' created!")
        print(f"   Credentials: Username = HADJIAhmed, Password = {admin_password}")
    else:
        print("👤 Default admin account 'HADJIAhmed' already exists.")
        
    # 6. Save GOOGLE_CREDS string to a .env file or print it
    print("\n========================================")
    print("🎉 Google Sheet Setup Complete!")
    print("========================================")
    print("\nTo run the app, you need to set the GOOGLE_CREDS environment variable.")
    print("I will write a local '.env' file containing this credential string so the Flask server can read it automatically.\n")
    
    env_content = f"GOOGLE_CREDS={json.dumps(creds_data)}\n"
    with open(".env", "w") as env_file:
        env_file.write(env_content)
        
    print("✅ Created '.env' file successfully with your credentials!")
    print("Next step: Run the web application.")

if __name__ == "__main__":
    main()
