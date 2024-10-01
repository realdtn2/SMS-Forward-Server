import re
import json
import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from werkzeug.security import generate_password_hash, check_password_hash

DISPLAY_NAME_FILE = 'display_names.json'

def load_display_names():
    if os.path.exists(DISPLAY_NAME_FILE):
        with open(DISPLAY_NAME_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_display_names(display_names):
    with open(DISPLAY_NAME_FILE, 'w') as f:
        json.dump(display_names, f)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sms.db'
app.config['SECRET_KEY'] = 'mysecret'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class SMS(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    from_number = db.Column(db.String(10), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    sms_type = db.Column(db.String(20), nullable=False)  # This will store the SMS type

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
@login_required
def index():
    sms_types = SMS.query.with_entities(SMS.sms_type).distinct().all()
    display_names = load_display_names()  # Load display names from the file
    return render_template('index.html', sms_types=sms_types, display_names=display_names)


@app.route('/sms<sms_type>', methods=['GET'])
@login_required
def messages(sms_type):
    # Retrieve messages for the given sms_type
    messages = SMS.query.filter_by(sms_type=sms_type).all()

    # Retrieve unique "from" numbers for the given sms_type
    from_numbers = SMS.query.with_entities(SMS.from_number).filter_by(sms_type=sms_type).distinct().all()
    from_numbers = [num[0] for num in from_numbers]  # Extract the numbers

    # Check if the sms_type is a main path (like /sms1 or /sms190321390218039)
    if re.match(r'^[0-9]+$', sms_type):  # Ensure sms_type consists of digits only
        return render_template('messages_no_section.html', from_number=sms_type, messages=messages, from_numbers=from_numbers)

    # Default to the regular messages.html for any other paths
    return render_template('messages.html', from_number=sms_type, messages=messages, from_numbers=from_numbers)

@app.route('/sms/<sms_type>/<from_number>', methods=['GET'])
@login_required
def messages_by_from(sms_type, from_number):
    # Retrieve messages for the specific sender
    messages = SMS.query.filter_by(sms_type=sms_type, from_number=from_number).all()

    # Retrieve unique "from" numbers for the given sms_type
    from_numbers = SMS.query.with_entities(SMS.from_number).filter_by(sms_type=sms_type).distinct().all()
    from_numbers = list(set(num[0] for num in from_numbers))  # Convert to a set and back to a list to ensure uniqueness

    return render_template(
        'messages.html',
        from_number=sms_type,
        messages=messages,
        from_numbers=from_numbers,
        selected_sender=from_number  # Pass the selected sender to the template
    )

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):  # Secure password check
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'danger')  # Flash message for failed login
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/sms<sms_type>', methods=['POST'])
def receive_sms(sms_type):
    data = request.json
    from_number = data.get('from')
    message = data.get('message')

    if from_number and message:
        new_sms = SMS(from_number=from_number, message=message, sms_type=sms_type)
        db.session.add(new_sms)
        db.session.commit()
    return 'SMS Received', 200

@app.route('/rename_sms/<sms_type>', methods=['POST'])
@login_required
def rename_sms(sms_type):
    new_display_name = request.form.get('new_sms_type')

    if new_display_name:
        # Load existing display names
        display_names = load_display_names()

        # Update the display name for the given sms_type
        display_names[sms_type] = new_display_name

        # Save the updated display names back to the file
        save_display_names(display_names)

        flash(f'Display name for SMS type {sms_type} updated to {new_display_name}', 'success')
        return redirect(url_for('index'))  # Redirect to the index page instead of the messages page
    else:
        flash('New display name not provided', 'danger')
        return redirect(url_for('index'))  # Redirect to the index page on failure as well

@app.route('/delete_sms/<int:sms_id>', methods=['POST'])
@login_required
def delete_sms(sms_id):
    sms = SMS.query.get(sms_id)
    if sms:
        db.session.delete(sms)
        db.session.commit()
        flash('Message deleted successfully', 'success')
    else:
        flash('Message not found', 'danger')
    return redirect(url_for('messages', sms_type=sms.sms_type))


@app.route('/delete_messages_from_number/<sms_type>', methods=['POST'])
@login_required
def delete_messages_from_number(sms_type):
    messages = SMS.query.filter_by(sms_type=sms_type).all()
    for msg in messages:
        db.session.delete(msg)
    db.session.commit()
    flash(f'All messages from {sms_type} deleted successfully', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='username').first():
            hashed_password = generate_password_hash('password')
            new_user = User(username='username', password=hashed_password)
            db.session.add(new_user)
            db.session.commit()

    app.run
