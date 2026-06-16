# 🐄 Animal Management System

A web-based livestock tracking system using RFID technology, built with Flask, Google Sheets, and Python.

## 🌟 Features

- RFID animal tracking
- Breeder account management
- Admin dashboard
- Data synchronization
- Vaccination records
- Registration request system
- **Real-time Alert Listener (Google Sheets)**: Sends email notifications to breeders and administrators when an animal's alert state changes.

---

## ⚙️ Real-time Alert Email Listener Setup

The hardware device updates the Google Sheet directly. To receive real-time email notifications whenever a new alert occurs, follow these steps to set up the Google Apps Script listener:

### 1. Open Apps Script Editor
1. Open your Google Sheet (`Animal_management`).
2. Click on **Extensions** in the top menu, then select **Apps Script**.

### 2. Add the Code
1. Delete any code in the editor (typically `Code.gs`).
2. Open the file [apps_script_code.js](apps_script_code.js) from this repository.
3. Copy the entire contents of `apps_script_code.js` and paste it into the Apps Script editor.
4. Click the **Save** icon (disk symbol) or press `Ctrl + S`.

### 3. Deploy as a Web App
1. Click the **Deploy** button at the top right and select **New deployment**.
2. Click the gear icon next to "Select type" and choose **Web app**.
3. Configure the settings:
   - **Description**: `Animal Management Sync and Alerts`
   - **Execute as**: `Me (your-gmail-address@gmail.com)`
   - **Who has access**: `Anyone` (This allows the local hardware receiver to send updates without requiring Google authentication).
4. Click **Deploy**.
5. You may be prompted to authorize access. Click **Authorize access**, choose your Google account, click **Advanced**, and then click **Go to Untitled project (unsafe)** to grant the necessary permissions.
6. Copy the **Web App URL** provided. It will look like this:
   `https://script.google.com/macros/s/XXXXX/exec`

### 4. Update the Hardware / Receiver URL
1. Update your hardware local receiver configuration (e.g. `recepteur base local.txt` line 2008) or sync tools to send requests to your new Web App URL.

---

## 🏃 Running the Flask Web Application Locally

### 1. Set up virtual environment
```bash
python -m venv venv
venv\Scripts\activate  # On Windows
source venv/bin/activate  # On macOS/Linux
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Setup credentials
Ensure you run `initialize_sheets.py` or place your Google Service Account `credentials.json` in the root folder.

### 4. Run Flask Server
```bash
python app.py
```
Access the system at: http://localhost:5000

---

## 👥 Default User Accounts
| Role | Username | Password |
|---|---|---|
| Admin | `HADJIAhmed` | `07No1986/` |
| Breeder 1 | `ttest` | `zk,w*mdIM+` |
| Breeder 2 | `bahmed` | `7L"bH+i("C` |

---

## 📧 Support
For support contact: ahmed.hadji2219@gmail.com
*Developed at University of Sidi Bel Abbes - Startup Project 2024/2025*
