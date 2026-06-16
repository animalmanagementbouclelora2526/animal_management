import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Ensure GOOGLE_CREDS is set in env before importing app
os.environ["GOOGLE_CREDS"] = '{"type": "service_account", "project_id": "dummy"}'

# Setup mocks for gspread and Google OAuth
mock_gspread = MagicMock()
mock_oauth = MagicMock()
sys.modules['gspread'] = mock_gspread
sys.modules['google.oauth2.service_account'] = mock_oauth

# Mock Credentials
mock_creds = MagicMock()
mock_oauth.Credentials.from_service_account_info.return_value = mock_creds

# Mock Spreadsheet client
mock_client = MagicMock()
mock_gspread.authorize.return_value = mock_client
mock_spreadsheet = MagicMock()
mock_client.open.return_value = mock_spreadsheet
mock_client.open_by_key.return_value = mock_spreadsheet

# Worksheets
mock_users_sheet = MagicMock()
mock_requests_sheet = MagicMock()
mock_animals_sheet = MagicMock()
mock_positions_sheet = MagicMock()
mock_alerts_sheet = MagicMock()

def get_worksheet(name):
    if name == "Users":
        return mock_users_sheet
    elif name == "Registration_requests":
        return mock_requests_sheet
    elif name == "Animal":
        return mock_animals_sheet
    elif name == "positions_history":
        return mock_positions_sheet
    elif name == "alerts_history":
        return mock_alerts_sheet
    return MagicMock()

mock_spreadsheet.worksheet.side_effect = get_worksheet

# Import the app module
import app

class TestAnimalDeathOrSale(unittest.TestCase):
    def setUp(self):
        mock_users_sheet.reset_mock()
        mock_animals_sheet.reset_mock()
        
        # Default mock users with Breeder IDs 3 and 4
        mock_users_sheet.get_all_records.return_value = [
            {"Eleveur_ID": "3", "Username": "breeder1", "Password": "password", "Role": "éleveur", "Email": "sidoa065@gmail.com"},
            {"Eleveur_ID": "4", "Username": "breeder2", "Password": "password", "Role": "éleveur", "Email": "sidoa065@gmail.com"},
            {"Eleveur_ID": "5", "Username": "HADJIAhmed", "Password": "password", "Role": "admin", "Email": "sidoa065@gmail.com"}
        ]
        
    def tearDown(self):
        # Cancel all active sync timers to prevent them from firing after the test ends
        for timer in list(app.sync_timer.values()):
            timer.cancel()
        app.sync_timer.clear()
        app.sync_cache.clear()
        
    @patch('app.send_email_async')
    def test_animal_reported_deceased_mort(self, mock_send_email):
        # Scenario: Animal status changes from ACTIVE to MORT under Breeder 3
        mock_animals_sheet.get_all_records.return_value = [
            {
                "ID": "1",
                "MAC": "00:1A:2B:3C:4D:5E",
                "Category": "Bovin",
                "Gender": "Female",
                "Birth_date": "2021-04-12",
                "Vaccines": "Vaccine A",
                "Latitude": "35.1982",
                "Longitude": "-0.6278",
                "Battery_status": "92",
                "Aler_Hist": "None",
                "Animal_status": "ACTIVE",
                "Farmer_ID": "3",
                "Last_Sync": ""
            }
        ]
        
        with app.app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user_id'] = "3" # Breeder 3
                sess['username'] = "breeder1"
                sess['role'] = "éleveur"
                
            payload = {
                "animals": [
                    {
                        "mac": "00:1A:2B:3C:4D:5E",
                        "category": "Bovin",
                        "gender": "Female",
                        "Birth_date": "2021-04-12",
                        "vaccines": "Vaccine A",
                        "Latitude": "35.1982",
                        "Longitude": "-0.6278",
                        "Battery_status": "92",
                        "Aler_Hist": "None",
                        "Animal_status": "MORT"
                    }
                ]
            }
            
            response = client.post('/sync_animals', json=payload)
            self.assertEqual(response.status_code, 200)
            
            # Verify database was updated
            mock_animals_sheet.update.assert_called()
            
            # Verify notifications sent to Breeder and Administrator
            recipients = [call.args[0] for call in mock_send_email.call_args_list]
            self.assertIn("sidoa065@gmail.com", recipients)
            
            # Verify email subject
            subjects = [call.args[1] for call in mock_send_email.call_args_list]
            self.assertTrue(any("MORT" in subj or "Deceased" in subj for subj in subjects))
            print("Test Animal Deceased (MORT) passed successfully!")

    @patch('app.send_email_async')
    def test_animal_reported_sold_vendu(self, mock_send_email):
        # Scenario: Animal with MAC '00:1A:2B:3C:4D:5E' currently belongs to Breeder 3.
        # Breeder 4 syncs the animal, which means it has been sold to Breeder 4 (Farmer_ID changes from 3 to 4).
        mock_animals_sheet.get_all_records.return_value = [
            {
                "ID": "1",
                "MAC": "00:1A:2B:3C:4D:5E",
                "Category": "Bovin",
                "Gender": "Female",
                "Birth_date": "2021-04-12",
                "Vaccines": "Vaccine A",
                "Latitude": "35.1982",
                "Longitude": "-0.6278",
                "Battery_status": "92",
                "Aler_Hist": "None",
                "Animal_status": "VENDU",
                "Farmer_ID": "3", # Belonging to Breeder 3
                "Last_Sync": ""
            }
        ]
        
        with app.app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user_id'] = "4" # Synced by Breeder 4
                sess['username'] = "breeder2"
                sess['role'] = "éleveur"
                
            payload = {
                "animals": [
                    {
                        "mac": "00:1A:2B:3C:4D:5E",
                        "category": "Bovin",
                        "gender": "Female",
                        "Birth_date": "2021-04-12",
                        "vaccines": "Vaccine A",
                        "Latitude": "35.1982",
                        "Longitude": "-0.6278",
                        "Battery_status": "92",
                        "Aler_Hist": "None",
                        "Animal_status": "ACTIVE"
                    }
                ]
            }
            
            response = client.post('/sync_animals', json=payload)
            self.assertEqual(response.status_code, 200)
            
            # Verify database updated
            mock_animals_sheet.update.assert_called()
            
            # Verify notifications sent to Breeder and Administrator
            recipients = [call.args[0] for call in mock_send_email.call_args_list]
            self.assertIn("sidoa065@gmail.com", recipients)
            
            # Verify email subject
            subjects = [call.args[1] for call in mock_send_email.call_args_list]
            self.assertTrue(any("VENDU" in subj or "Sale" in subj for subj in subjects))
            print("Test Animal Sale (VENDU) passed successfully!")

if __name__ == '__main__':
    unittest.main()
