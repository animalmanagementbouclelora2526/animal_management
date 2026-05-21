from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_mysqldb import MySQL
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from werkzeug.security import generate_password_hash, check_password_hash
import random
import string

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '07No1986/'
app.config['MYSQL_DB'] = 'Animal_management'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

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
        
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM Users WHERE Username = %s", (username,))
        user = cur.fetchone()
        cur.close()
        
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
        
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO Registration_requests (Name, First_name, Email, Card_number) VALUES (%s, %s, %s, %s)",
                    (name, first_name, email, card_number))
        mysql.connection.commit()
        cur.close()
        
        # Send notification email to admin
        admin_emails = []
        cur = mysql.connection.cursor()
        cur.execute("SELECT Email FROM Users WHERE Role = 'admin'")
        admins = cur.fetchall()
        cur.close()
        
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
    
    cur = mysql.connection.cursor()
    
    # Get all eleveurs and their animals
    cur.execute("""
        SELECT u.Eleveur_ID, u.Username, u.Email, 
               COUNT(a.ID) as animal_count,
               MAX(a.Last_sync) as last_sync
        FROM Users u
        LEFT JOIN Animal a ON u.Eleveur_ID = a.Eleveur_ID
        WHERE u.Role = 'éleveur'
        GROUP BY u.Eleveur_ID
    """)
    eleveurs = cur.fetchall()
    
    cur.close()
    return render_template('admin/dashboard.html', eleveurs=eleveurs)

@app.route('/admin/requests')
def admin_requests():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM Registration_requests WHERE Status = 'en attente'")
    requests = cur.fetchall()
    cur.close()
    
    return render_template('admin/requests.html', requests=requests)

@app.route('/admin/process_request/<int:request_id>/<action>')
def process_request(request_id, action):
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    cur = mysql.connection.cursor()
    
    # Get the request
    cur.execute("SELECT * FROM Registration_requests WHERE ID = %s", (request_id,))
    req = cur.fetchone()
    
    if not req:
        flash('Request not found', 'danger')
        return redirect(url_for('admin_requests'))
    
    if action == 'accept':
        # Generate username and password
        username = req['First_name'][0].lower() + req['Name'].lower()
        password = generate_password()
        
        # Check if username already exists
        cur.execute("SELECT * FROM Users WHERE Username = %s", (username,))
        if cur.fetchone():
            # Add a number if username exists
            counter = 1
            while True:
                new_username = f"{username}{counter}"
                cur.execute("SELECT * FROM Users WHERE Username = %s", (new_username,))
                if not cur.fetchone():
                    username = new_username
                    break
                counter += 1
        
        # Create user
        hashed_password = generate_password_hash(password)
        cur.execute("""
            INSERT INTO Users (Username, Password, Role, Email)
            VALUES (%s, %s, 'éleveur', %s)
        """, (username, hashed_password, req['Email']))
        mysql.connection.commit()
        
        # Update request status
        cur.execute("""
            UPDATE Registration_requests 
            SET Status = 'accepté' 
            WHERE ID = %s
        """, (request_id,))
        mysql.connection.commit()
        
        # Send email to the new user
        subject = "Your Registration Has Been Approved"
        body = f"""Dear {req['First_name']} {req['Name']},
        
Your registration request has been approved. Here are your login credentials:

Username: {username}
Password: {password}

Please log in to the system and change your password as soon as possible.

Best regards,
Animal Management System Team"""
        
        send_email(req['Email'], subject, body)
        
        flash('Request approved and user created', 'success')
    
    elif action == 'reject':
        # Update request status
        cur.execute("""
            UPDATE Registration_requests 
            SET Status = 'refusé' 
            WHERE ID = %s
        """, (request_id,))
        mysql.connection.commit()
        
        # Send email to the requester
        subject = "Your Registration Has Been Rejected"
        body = f"""Dear {req['First_name']} {req['Name']},
        
We regret to inform you that your registration request has been rejected.

If you believe this is a mistake, please contact the administrator.

Best regards,
Animal Management System Team"""
        
        send_email(req['Email'], subject, body)
        
        flash('Request rejected', 'info')
    
    cur.close()
    return redirect(url_for('admin_requests'))

@app.route('/eleveur/dashboard')
def eleveur_dashboard():
    if 'user_id' not in session or session['role'] != 'éleveur':
        return redirect(url_for('login'))
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM Animal WHERE Eleveur_ID = %s", (session['user_id'],))
    animals = cur.fetchall()
    cur.close()
    
    return render_template('eleveur/dashboard.html', animals=animals)

@app.route('/sync_animals', methods=['POST'])
def sync_animals():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authenticated'}), 401
    
    data = request.json
    eleveur_id = session['user_id']
    
    if not data or 'animals' not in data:
        return jsonify({'status': 'error', 'message': 'Invalid data format'}), 400
    
    try:
        cur = mysql.connection.cursor()
        
        # Delete all existing animals for this eleveur
        cur.execute("DELETE FROM Animal WHERE Eleveur_ID = %s", (eleveur_id,))
        
        # Insert new animals
        for animal in data['animals']:
            cur.execute("""
                INSERT INTO Animal (RFID_tag, Category, Gender, Birth_date, Vaccines, Eleveur_ID)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                animal['rfid_tag'],
                animal['category'],
                animal['gender'],
                animal['birth_date'],
                animal['vaccines'],
                eleveur_id
            ))
        
        mysql.connection.commit()
        cur.close()
        
        return jsonify({'status': 'success', 'message': 'Animals synchronized successfully'})
    
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/admin/breeder_animals/<int:breeder_id>')
def breeder_animals(breeder_id):
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    cur = mysql.connection.cursor()
    
    # Get breeder info
    cur.execute("SELECT Username FROM Users WHERE Eleveur_ID = %s", (breeder_id,))
    breeder = cur.fetchone()
    
    # Get animals
    cur.execute("""
        SELECT a.*, u.Username 
        FROM Animal a
        JOIN Users u ON a.Eleveur_ID = u.Eleveur_ID
        WHERE a.Eleveur_ID = %s
    """, (breeder_id,))
    animals = cur.fetchall()
    
    cur.close()
    
    return render_template('admin/breeder_animals.html', 
                         animals=animals, 
                         breeder=breeder)


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
        cur = mysql.connection.cursor()
        cur.execute("SELECT Email FROM Users WHERE Role = 'éleveur'")
        eleveurs = cur.fetchall()
        cur.close()
        
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
