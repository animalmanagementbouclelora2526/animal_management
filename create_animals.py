import json
import os
import gspread
from datetime import datetime
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def run():
    creds_path = "animaltracker-499320-0c2c76b1a2ff.json"
    if not os.path.exists(creds_path):
        print(f"Error: Credentials file '{creds_path}' not found.")
        return
        
    print("Reading credentials...")
    with open(creds_path, 'r') as f:
        creds_data = json.load(f)
        
    try:
        creds = Credentials.from_service_account_info(creds_data, scopes=SCOPES)
        client = gspread.authorize(creds)
        spreadsheet = client.open("Animal_management")
        animals_sheet = spreadsheet.worksheet("Animal")
        print("Connected to Google Sheets successfully.")
    except Exception as e:
        print(f"Error connecting: {e}")
        return
        
    # Sample animal records for Farmer_ID = 1
    # Schema: ID, MAC, Category, Gender, Birth_date, Vaccines, Latitude, Longitude, Battery_status, Aler_Hist, Animal_status, Farmer_ID, Last_Sync
    now_str = str(datetime.now())
    sample_animals = [
        [
            1, 
            "00:1A:2B:3C:4D:5E", 
            "Bovin", 
            "Female", 
            "2021-04-12", 
            "Vaccine A, Vaccine B", 
            "35.1982", 
            "-0.6278", 
            "92", 
            "None", 
            "ACTIVE", 
            1, 
            now_str
        ],
        [
            2, 
            "00:1A:2B:3C:4D:5F", 
            "Ovin", 
            "Male", 
            "2023-08-20", 
            "Vaccine C", 
            "35.2015", 
            "-0.6302", 
            "18", 
            "ALERTE: Battery critical", 
            "ALERTE", 
            1, 
            now_str
        ],
        [
            3, 
            "00:1A:2B:3C:4D:60", 
            "Caprin", 
            "Female", 
            "2022-11-05", 
            "None", 
            "35.1950", 
            "-0.6220", 
            "45", 
            "None", 
            "ACTIVE", 
            1, 
            now_str
        ]
    ]
    
    print("Clearing any existing animal records (excluding headers) and inserting sample animals...")
    try:
        # Keep header row, clear all rows from row 2 onwards
        # In gspread, we can just delete from row 2 to 100 or recreate
        # To be safe, we append if empty, or overwrite
        records = animals_sheet.get_all_records()
        if len(records) > 0:
            # Overwrite rows starting from index 2
            for i, row_data in enumerate(sample_animals, start=2):
                animals_sheet.update(f"A{i}:M{i}", [row_data])
        else:
            for row_data in sample_animals:
                animals_sheet.append_row(row_data)
        print("Successfully created 3 sample animals assigned to Farmer_ID = 1!")
    except Exception as e:
        print(f"Error inserting records: {e}")

    print("Inserting sample position history records...")
    try:
        positions_sheet = spreadsheet.worksheet("positions_history")
        # Sample positions list
        sample_positions = [
            [1, "00:1A:2B:3C:4D:5E", "35.1980", "-0.6270", "2026-06-14 09:00:00", 1],
            [2, "00:1A:2B:3C:4D:5E", "35.1982", "-0.6278", "2026-06-14 10:00:00", 1],
            [3, "00:1A:2B:3C:4D:5F", "35.2010", "-0.6300", "2026-06-14 09:15:00", 2],
            [4, "00:1A:2B:3C:4D:5F", "35.2015", "-0.6302", "2026-06-14 10:15:00", 2],
            [5, "00:1A:2B:3C:4D:60", "35.1945", "-0.6215", "2026-06-14 09:30:00", 3],
            [6, "00:1A:2B:3C:4D:60", "35.1950", "-0.6220", "2026-06-14 10:30:00", 3]
        ]
        
        # Overwrite rows starting from index 2
        for i, row_data in enumerate(sample_positions, start=2):
            positions_sheet.update(f"A{i}:F{i}", [row_data])
        print("Successfully created 6 sample position history records!")
    except Exception as e:
        print(f"Error inserting position history: {e}")

if __name__ == "__main__":
    run()
