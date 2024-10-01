import os
from app import app, db, User
from werkzeug.security import generate_password_hash

# Delete the existing database
db_file = 'sms.db'
if os.path.exists(db_file):
    os.remove(db_file)
    print(f"{db_file} deleted.")

with app.app_context():
    # Create the database and tables
    db.create_all()  
