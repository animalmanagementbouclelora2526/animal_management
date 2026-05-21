# 🐄 Animal Management System

A web-based livestock tracking system using RFID technology, built with Flask, MySQL, and Python.

![System Overview](static/images/system_overview.png) *Replace with your actual screenshot*

## 🌟 Features

- RFID animal tracking
- Breeder account management
- Admin dashboard
- Data synchronization
- Vaccination records
- Registration request system

## 🛠️ Prerequisites

- Python 3.8+
- MySQL 5.7+
- pip package manager
- Git (optional)

## 🚀 Installation

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/animal-management.git
cd animal-management

2. Set up virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

3. Install dependencies
pip install -r requirements.txt

4. Database Setup
mysql -u root -p < database_setup.sql

⚙️ Configuration

    Create .env file:

ini

SECRET_KEY=your_secret_key_here
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_DB=Animal_management

    Initialize database with admin account:

bash

python initialize_db.py

🏃 Running the Application
bash

flask run

Access the system at: http://localhost:5000
👥 User Accounts
Role	Username	Password
Admin	HADJIAhmed	07No1986/
Breeder	(Created via registration)	(Auto-generated)
🔄 Synchronization
Manual Sync (Web Interface)

    Login as breeder

    Click "Sync Animals" button

    Upload JSON data from RFID reader

API Endpoint
bash

POST /sync_animals
Content-Type: application/json

{
  "animals": [
    {
      "rfid_tag": "RFID1001",
      "category": "Bovin",
      "gender": "Male",
      "birth_date": "2020-05-15",
      "vaccines": "Vaccine A, Vaccine B"
    }
  ]
}

📂 Project Structure
text

animal-management/
├── app.py                # Main application
├── config.py             # Configuration
├── static/               # Static files
│   ├── css/              # Stylesheets
│   └── images/           # System images
├── templates/            # HTML templates
├── database_setup.sql    # Database schema
└── requirements.txt      # Dependencies

🐛 Troubleshooting

Issue: Can't login as admin

    Verify admin exists in database:
    sql

SELECT * FROM Users WHERE Username = 'HADJIAhmed';

Reset admin password:
bash

    python reset_admin.py

Issue: Database connection errors

    Verify MySQL service is running

    Check .env file credentials

📧 Contact

For support contact: ahmed.hadji2219@gmail.com

*Developed at University of Sidi Bel Abbes - Startup Project 2024/2025*
text


### Key Sections Explained:

1. **Visual Introduction**: Replace the placeholder image with your actual system screenshot

2. **Installation Steps**: Includes both Unix and Windows commands

3. **Configuration**: Highlights critical environment variables

4. **User Accounts**: Clearly shows default credentials

5. **API Documentation**: Shows how to use the sync endpoint

6. **Troubleshooting**: Covers common issues you've encountered

7. **Project Structure**: Helps developers navigate the codebase

To use this README:
1. Save as `README.md` in your project root
2. Replace placeholder values with your actual information
3. Add real screenshots to the `static/images/` directory
4. Commit to your version control system

This professional README will help users and developers understand, install, and troubleshoot your system effectively.
