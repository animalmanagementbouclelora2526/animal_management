from app import create_app
from werkzeug.security import generate_password_hash
from flask_mysqldb import MySQL

app = create_app()  # Make sure your app factory exists
mysql = MySQL(app)

def update_admin_password():
    try:
        with app.app_context():
            cur = mysql.connection.cursor()
            hashed_password = generate_password_hash('07No1986/')
            
            # Update the admin password
            cur.execute(
                "UPDATE Users SET Password = %s WHERE Username = 'HADJIAhmed'",
                (hashed_password,)
            )
            mysql.connection.commit()
            print("Admin password updated successfully!")
    except Exception as e:
        print(f"Error updating admin password: {e}")
    finally:
        if 'cur' in locals():
            cur.close()

if __name__ == '__main__':
    update_admin_password()