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

import json
import os
from google.oauth2.service_account import Credentials
import threading

info = json.loads(os.environ["GOOGLE_CREDS"])

creds = Credentials.from_service_account_info(info, scopes=SCOPES)

client = gspread.authorize(creds)
spreadsheet = client.open("Animal_management")

users_sheet = spreadsheet.worksheet("Users")
requests_sheet = spreadsheet.worksheet("Registration_requests")
animals_sheet = spreadsheet.worksheet("Animal")
positions_sheet = spreadsheet.worksheet("positions_history")
alerts_sheet = spreadsheet.worksheet("alerts_history")

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'


# Email Configuration
EMAIL_ADDRESS = 'ahmed.hadji2219@gmail.com'
EMAIL_PASSWORD = 'ussi gxpf jpax baxy'
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
sync_cache = {}
sync_timer = {}


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
def get_admin_emails():

    admins = []

    for user in users_sheet.get_all_records():

        if user['Role'] == 'admin':

            admins.append(user['Email'])

    return admins
    
def get_farmer_email(farmer_id):

    for user in users_sheet.get_all_records():

        if str(user['Eleveur_ID']) == str(farmer_id):

            return user['Email']

    return None
    
def send_sync_summary(farmer_id):

    if farmer_id not in sync_cache:
        return

    animals = sync_cache[farmer_id]

    body = "The following animals have been synchronized:\n\n"

    for i, mac in enumerate(animals):

        body += f"{i+1}. {mac}\n"

    # email éleveur
    farmer_email = get_farmer_email(farmer_id)

    if farmer_email:

        send_email(
            farmer_email,
            "Synchronization Summary",
            body
        )

    # email admins
    for admin_email in get_admin_emails():

        send_email(
            admin_email,
            f"Synchronization Summary Farmer {farmer_id}",
            body
        )

    # vider le cache
    del sync_cache[farmer_id]

    if farmer_id in sync_timer:
        del sync_timer[farmer_id]

def add_sync_to_cache(farmer_id, mac):

    if farmer_id not in sync_cache:

        sync_cache[farmer_id] = []

    # éviter les doublons
    if mac not in sync_cache[farmer_id]:

        sync_cache[farmer_id].append(mac)

    # timer déjà lancé ?
    if farmer_id in sync_timer:

        return

    timer = threading.Timer(
        35,
        send_sync_summary,
        args=[farmer_id]
    )

    sync_timer[farmer_id] = timer

    timer.start()


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
@app.route('/animal/<mac>')
def animal_details(mac):

    if 'user_id' not in session:
        return redirect(url_for('login'))

    animals = animals_sheet.get_all_records()

    animal = None

    for a in animals:

        if a['MAC'] == mac:
            animal = a
            break

    if animal is None:

        flash('Animal not found')

        if session['role'] == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('eleveur_dashboard'))

    return render_template(
        'animal_details.html',
        animal=animal
    )
@app.route('/position_history/<mac>')
def position_history(mac):

    if 'user_id' not in session:
        return redirect(url_for('login'))

    animal = None

    for a in animals_sheet.get_all_records():

        if a['MAC'] == mac:
            animal = a
            break

    if animal is None:

        flash('Animal not found')

        if session['role'] == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('eleveur_dashboard'))

    positions = []

    for row in positions_sheet.get_all_records():

        if row['MAC'] == mac:

            positions.append({
                'lat': float(row['Latitude']),
                'lon': float(row['Longitude']),
                'date': row['Date']
            })

    return render_template(
        'position_history.html',
        animal=animal,
        positions=positions
    )
##############################################################################################################################################
@app.route('/admin/dashboard')
def admin_dashboard():

    if 'user_id' not in session or session['role'] != 'admin':

        return redirect(url_for('login'))

    users = users_sheet.get_all_records()
    animals = animals_sheet.get_all_records()

    eleveurs = []

    for user in users:

        if user['Role'] != 'éleveur':
            continue

        animal_count = 0
        alert_count = 0
        low_battery_count = 0
        last_sync = None

        for animal in animals:

            if str(animal['Farmer_ID']) == str(user['Eleveur_ID']):

                animal_count += 1

                # dernière synchronisation
                if animal['Last_Sync'] != '':
                    if last_sync is None or str(animal['Last_Sync']) > str(last_sync):
                        last_sync = animal['Last_Sync']

                # animal en alerte
                if str(animal['Animal_status']).upper() == "ALERTE":
                    alert_count += 1

                # batterie faible
                try:
                    if int(animal['Battery_status']) < 20:
                        low_battery_count += 1
                except:
                    pass

        eleveurs.append({

            'Eleveur_ID': user['Eleveur_ID'],
            'Username': user['Username'],
            'Email': user['Email'],
            'animal_count': animal_count,
            'alert_count': alert_count,
            'low_battery_count': low_battery_count,
            'last_sync': last_sync

        })

    return render_template(
        'admin/dashboard.html',
        eleveurs=eleveurs
    )
@app.route('/admin/requests')
def admin_requests():

    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    pending_requests = []

    for req in requests_sheet.get_all_records():

        status = str(req.get('Status', '')).strip().lower()

        if status == 'en attente':
            pending_requests.append(req)

    return render_template(
        'admin/requests.html',
        requests=pending_requests
    )
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
###################################################################################################################
@app.route('/eleveur/dashboard')
def eleveur_dashboard():

    if 'user_id' not in session or session['role'] != 'éleveur':
        return redirect(url_for('login'))

    animals = []

    all_animals = animals_sheet.get_all_records()

    for animal in all_animals:

        if str(animal.get('Farmer_ID', '')).strip() == str(session['user_id']):
            animals.append(animal)

    return render_template(
        'eleveur/dashboard.html',
        animals=animals
    )

@app.route('/sync_animals', methods=['POST'])
def sync_animals():

    if 'user_id' not in session:
        return jsonify({
            'status': 'error',
            'message': 'Not authenticated'
        }), 401

    data = request.json
    farmer_id = session['user_id']

    if not data or 'animals' not in data:
        return jsonify({
            'status': 'error',
            'message': 'Invalid data format'
        }), 400

    try:

        animals = animals_sheet.get_all_records()

        for animal in data['animals']:

            mac = animal['mac']

            existing_animal = None
            row_index = None

            for i, row in enumerate(animals, start=2):

                if row['MAC'] == mac:
                    existing_animal = row
                    row_index = i
                    break

            # ==========================
            # NOUVEL ANIMAL
            # ==========================
            if existing_animal is None:

                animals_sheet.append_row([

                    len(animals) + 1,
                    mac,
                    animal['category'],
                    animal['gender'],
                    animal['Birth_date'],
                    animal['vaccines'],
                    animal['Latitude'],
                    animal['Longitude'],
                    animal['Battery_status'],
                    animal['Aler_Hist'],
                    animal['Animal_status'],
                    farmer_id,
                    str(datetime.now())

                ])

                add_sync_to_cache(farmer_id, mac)

            # ==========================
            # MEME ELEVEUR
            # ==========================
            elif str(existing_animal['Farmer_ID']) == str(farmer_id):

                previous_alert = existing_animal['Aler_Hist']

                animals_sheet.update(
                    f"A{row_index}:M{row_index}",
                    [[

                        existing_animal['ID'],
                        mac,
                        animal['category'],
                        animal['gender'],
                        animal['Birth_date'],
                        animal['vaccines'],
                        animal['Latitude'],
                        animal['Longitude'],
                        animal['Battery_status'],
                        animal['Aler_Hist'],
                        animal['Animal_status'],
                        farmer_id,
                        str(datetime.now())

                    ]]
                )

                add_sync_to_cache(farmer_id, mac)

                # Nouvelle alerte
                if (
                    previous_alert != animal['Aler_Hist']
                    and animal['Aler_Hist'] != ""
                ):

                    alerts_sheet.append_row([

                        len(alerts_sheet.get_all_records()) + 1,
                        mac,
                        animal['Aler_Hist'],
                        animal['Latitude'],
                        animal['Longitude'],
                        str(datetime.now())

                    ])

                    subject = "Animal Alert"

                    body = f"""
Animal : {mac}

Alert :
{animal['Aler_Hist']}

Battery :
{animal['Battery_status']} %

Position :
https://www.google.com/maps?q={animal['Latitude']},{animal['Longitude']}

Date :
{datetime.now()}
"""

                    farmer_email = get_farmer_email(farmer_id)

                    if farmer_email:
                        send_email(
                            farmer_email,
                            subject,
                            body
                        )

                    for admin_email in get_admin_emails():
                        send_email(
                            admin_email,
                            subject,
                            body
                        )

            # ==========================
            # AUTRE ELEVEUR
            # ==========================
            else:

                # Transfert après décès
                if existing_animal['Animal_status'] == 'MORT':

                    animals_sheet.update(
                        f"A{row_index}:M{row_index}",
                        [[

                            existing_animal['ID'],
                            mac,
                            animal['category'],
                            animal['gender'],
                            animal['Birth_date'],
                            animal['vaccines'],
                            animal['Latitude'],
                            animal['Longitude'],
                            animal['Battery_status'],
                            animal['Aler_Hist'],
                            'ACTIVE',
                            farmer_id,
                            str(datetime.now())

                        ]]
                    )

                    add_sync_to_cache(farmer_id, mac)

                    subject = "Animal transfer"

                    body = f"""
Animal {mac}

transferred to farmer {farmer_id}

because previous status was MORT.
"""

                    for admin_email in get_admin_emails():
                        send_email(
                            admin_email,
                            subject,
                            body
                        )

                else:

                    subject = "Duplicate registration attempt"

                    body = f"""
Animal {mac}

already belongs to another farmer.
"""

                    for admin_email in get_admin_emails():
                        send_email(
                            admin_email,
                            subject,
                            body
                        )

                    farmer_email = get_farmer_email(farmer_id)

                    if farmer_email:

                        send_email(
                            farmer_email,
                            "Registration refused",
                            body
                        )

                    continue

            # ==========================
            # HISTORIQUE DES POSITIONS
            # ==========================
            positions_sheet.append_row([

                len(positions_sheet.get_all_records()) + 1,
                mac,
                animal['Latitude'],
                animal['Longitude'],
                str(datetime.now())

            ])

        return jsonify({

            'status': 'success',
            'message': 'Synchronization completed'

        })

    except Exception as e:

        return jsonify({

            'status': 'error',
            'message': str(e)

        }), 500


##########################################################################################################################
@app.route('/admin/breeder_animals/<int:breeder_id>')
def breeder_animals(breeder_id):

    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    breeder = None

    users = users_sheet.get_all_records()

    for user in users:
        if str(user.get('Eleveur_ID', '')) == str(breeder_id):
            breeder = user
            break

    animals = []

    all_animals = animals_sheet.get_all_records()

    print("BREEDER_ID =", breeder_id)

    for animal in all_animals:

        print("FARMER_ID =", animal.get('Farmer_ID'))

        if str(animal.get('Farmer_ID', '')).strip() == str(breeder_id):

            print("MATCH FOUND")

            animal['Username'] = breeder.get('Username', '') if breeder else ''

            animals.append(animal)

    print("ANIMALS FINAL =", animals)

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
