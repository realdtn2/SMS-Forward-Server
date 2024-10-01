from app import app, db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    db.create_all()  # Create tables if they don't exist
    if not User.query.filter_by(username='realdtn').first():
        hashed_password = generate_password_hash('rdtn@17022008')  # No method specified
        new_user = User(username='realdtn', password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        print("User created:", new_user)
    else:
        print("User already exists.")
