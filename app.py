from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from werkzeug.security import generate_password_hash, check_password_hash
import random
import string
import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_file(
    "credentials.json",
    scopes=SCOPES
)

client = gspread.authorize(creds)
spreadsheet = client.open("Animal_management")

users_sheet = spreadsheet.worksheet("Users")
requests_sheet = spreadsheet.worksheet("Registration_requests")
animals_sheet = spreadsheet.worksheet("Animal")

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'


# Email Configuration
EMAIL_ADDRESS = 'ahmed.hadji2219@gmail.com'
EMAIL_PASSWORD = 'ussi gxpf jpax baxy'
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587

def send_email(to_email, subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_ADDRESS, to_email, text)
        server.quit()
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def generate_password():
    length = 10
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choice(characters) for i in range(length))
    return password

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
       
        users = users_sheet.get_all_records()

        user = None

        for u in users:
           if u['Username'] == username:
                user = u
                break
        
        if user:
            # Debug print (remove after testing)
            print(f"User found: {user['Username']}, DB Password: {user['Password']}")
            
            # Check both hashed and plain text password
            if (user['Password'].startswith('pbkdf2:') and 
                check_password_hash(user['Password'], password)) or \
                user['Password'] == password:
                
                session['user_id'] = user['Eleveur_ID']
                session['username'] = user['Username']
                session['role'] = user['Role']
                
                if user['Role'] == 'admin':
                    return redirect(url_for('admin_dashboard'))
                else:
                    return redirect(url_for('eleveur_dashboard'))
        
        flash('Invalid username or password', 'danger')
        return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/register_request', methods=['GET', 'POST'])
def register_request():
    if request.method == 'POST':
        name = request.form['name']
        first_name = request.form['first_name']
        email = request.form['email']
        card_number = request.form['card_number']
        
    
        requests_sheet.append_row([
            len(requests_sheet.get_all_records()) + 1,
            name,
            first_name,
            email,
            card_number,
            'en attente',
            str(datetime.now())
        ])
        
        # Send notification email to admin
        admin_emails = []
      
        admins = []

        for user in users_sheet.get_all_records():
            if user['Role'] == 'admin':
                admins.append(user)
        
        for admin in admins:
            admin_emails.append(admin['Email'])
        
        subject = "New Registration Request"
        body = f"A new registration request has been submitted:\n\nName: {name} {first_name}\nEmail: {email}\nCard Number: {card_number}"
        
        for email in admin_emails:
            send_email(email, subject, body)
        
        flash('Your registration request has been submitted. You will receive an email once it is processed.', 'success')
        return redirect(url_for('index'))
    
    return render_template('register.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    users = users_sheet.get_all_records()
    animals = animals_sheet.get_all_records()

    eleveurs = []

    for user in users:
        if user['Role'] == 'éleveur':

            animal_count = 0
            last_sync = ""

            for animal in animals:
                if str(animal['Eleveur_ID']) == str(user['Eleveur_ID']):
                    animal_count += 1
                    last_sync = animal['Last_sync']

            eleveurs.append({
                'Eleveur_ID': user['Eleveur_ID'],
                'Username': user['Username'],
                'Email': user['Email'],
                'animal_count': animal_count,
                'last_sync': last_sync
            })

    return render_template('admin/dashboard.html', eleveurs=eleveurs)

@app.route('/admin/requests')
def admin_requests():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    requests = []

    all_requests = requests_sheet.get_all_records()

    for req in all_requests:
        if req['Status'] == 'en attente':
            requests.append(req)

    return render_template('admin/requests.html', requests=requests)

@app.route('/admin/process_request/<int:request_id>/<action>')
def process_request(request_id, action):
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    requests = requests_sheet.get_all_records()

    req = None
    row_index = None

    for index, r in enumerate(requests, start=2):
        if int(r['ID']) == request_id:
            req = r
            row_index = index
            break

    if not req:
        flash('Request not found', 'danger')
        return redirect(url_for('admin_requests'))

    if action == 'accept':

        username = req['First_name'][0].lower() + req['Name'].lower()
        password = generate_password()

        users = users_sheet.get_all_records()

        existing_usernames = [u['Username'] for u in users]

        counter = 1
        original_username = username

        while username in existing_usernames:
            username = f"{original_username}{counter}"
            counter += 1

        hashed_password = generate_password_hash(password)

        new_id = len(users) + 1

        users_sheet.append_row([
            new_id,
            username,
            hashed_password,
            'éleveur',
            req['Email']
        ])

        requests_sheet.update_cell(row_index, 6, 'accepté')

        subject = "Your Registration Has Been Approved"

        body = f"""
Dear {req['First_name']} {req['Name']},

Your registration request has been approved.

Username: {username}
Password: {password}

Best regards,
Animal Management System Team
"""

        send_email(req['Email'], subject, body)

        flash('Request approved and user created', 'success')

    elif action == 'reject':

        requests_sheet.update_cell(row_index, 6, 'refusé')

        subject = "Your Registration Has Been Rejected"

        body = f"""
Dear {req['First_name']} {req['Name']},

We regret to inform you that your registration request has been rejected.

Best regards,
Animal Management System Team
"""

        send_email(req['Email'], subject, body)

        flash('Request rejected', 'info')

    return redirect(url_for('admin_requests'))

@app.route('/eleveur/dashboard')
def eleveur_dashboard():
    if 'user_id' not in session or session['role'] != 'éleveur':
        return redirect(url_for('login'))

    animals = []

    all_animals = animals_sheet.get_all_records()

    for animal in all_animals:
        if str(animal['Eleveur_ID']) == str(session['user_id']):
            animals.append(animal)

    return render_template('eleveur/dashboard.html', animals=animals)

@app.route('/sync_animals', methods=['POST'])
def sync_animals():

    if 'user_id' not in session:
        return jsonify({
            'status': 'error',
            'message': 'Not authenticated'
        }), 401

    data = request.json
    eleveur_id = session['user_id']

    if not data or 'animals' not in data:
        return jsonify({
            'status': 'error',
            'message': 'Invalid data format'
        }), 400

    try:

        for animal in data['animals']:

            animals_sheet.append_row([
                len(animals_sheet.get_all_records()) + 1,
                animal['rfid_tag'],
                animal['category'],
                animal['gender'],
                animal['birth_date'],
                animal['vaccines'],
                eleveur_id,
                str(datetime.now())
            ])

        return jsonify({
            'status': 'success',
            'message': 'Animals synchronized successfully'
        })

    except Exception as e:

        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/admin/breeder_animals/<int:breeder_id>')
def breeder_animals(breeder_id):
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    breeder = None

    users = users_sheet.get_all_records()

    for user in users:
        if str(user['Eleveur_ID']) == str(breeder_id):
            breeder = user
            break

    animals = []

    all_animals = animals_sheet.get_all_records()

    for animal in all_animals:
        if str(animal['Eleveur_ID']) == str(breeder_id):

            animal['Username'] = breeder['Username']

            animals.append(animal)

    return render_template(
        'admin/breeder_animals.html',
        animals=animals,
        breeder=breeder
    )


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

# Simulator for testing synchronization
@app.route('/simulator')
def simulator():
    return render_template('simulator.html')

@app.route('/simulate_sync', methods=['POST'])
def simulate_sync():
    if 'user_id' not in session or session['role'] != 'éleveur':
        return jsonify({'status': 'error', 'message': 'Not authenticated or not an eleveur'}), 401
    
    # Generate some test data
    test_animals = [
        {
            'rfid_tag': f"RFID{random.randint(1000, 9999)}",
            'category': 'Bovin',
            'gender': random.choice(['Male', 'Female']),
            'birth_date': f"202{random.randint(0, 3)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
            'vaccines': 'Vaccine A, Vaccine B'
        },
        {
            'rfid_tag': f"RFID{random.randint(1000, 9999)}",
            'category': 'Ovin',
            'gender': random.choice(['Male', 'Female']),
            'birth_date': f"202{random.randint(0, 3)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
            'vaccines': 'Vaccine C'
        }
    ]
    
    # Call the sync endpoint with test data
    response = app.test_client().post(
        '/sync_animals',
        json={'animals': test_animals},
        headers={'Content-Type': 'application/json'}
    )
    
    return response

# Monthly email notification job (would typically be set up as a cron job)
def send_monthly_notifications():

    with app.app_context():

        eleveurs = []

        for user in users_sheet.get_all_records():
            if user['Role'] == 'éleveur':
                eleveurs.append(user)

        subject = "Monthly Reminder: Synchronize Your Animals"

        body = """Dear Eleveur,

This is a monthly reminder to synchronize your animal data with the central database.

Please ensure all your animals' information is up to date.

Best regards,
Animal Management System Team"""

        for eleveur in eleveurs:
            send_email(eleveur['Email'], subject, body)

if __name__ == '__main__':
    app.run(debug=True) 