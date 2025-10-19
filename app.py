import os
import json
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session, Response
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient

# Use the standard Flask constructor
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a_default_secret_key_for_development_123')

# --- NEW: DATABASE CONNECTION ---
# We will set the MONGO_URI variable in our deployment host
# For local testing, it will try to connect to a local MongoDB instance if you have one
MONGO_URI = os.environ.get('MONGO_URI') 
if not MONGO_URI:
    print("WARNING: MONGO_URI not set. Deployment will fail.")
    # You can set a local fallback if you install MongoDB locally
    # For now, we'll rely on the one we set for the migration script
    
client = MongoClient(MONGO_URI)
db = client.ueldo_db # This is our database name
users_collection = db.users # This collection will store users
data_collection = db.data # This collection will store competitions
# ---------------------------------

# Admin auth
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', '1234')

# Decorator for admin auth (no changes)
def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if auth and auth.username == ADMIN_USERNAME and auth.password == ADMIN_PASSWORD:
            return f(*args, **kwargs)
        return Response(
            'Could not verify your access level for that URL.\n'
            'You must login with proper credentials.', 401,
            {'WWW-Authenticate': 'Basic realm="Login Required"'})
    return decorated

# --- NEW: DATABASE FUNCTIONS ---
def load_competitions():
    # Find the single document that holds all competition data
    data = data_collection.find_one({"_id": "competitions"})
    if data:
        # Remove the _id field so it looks just like the old JSON
        data.pop('_id', None)
        return data
    # If it doesn't exist (first run), return the empty structure
    return {"sports": {}, "creativity": {}, "socials": {}}

def save_competitions(competitions_data):
    # Update the single document, or create it if it doesn't exist
    data_collection.replace_one(
        {"_id": "competitions"},
        competitions_data,
        upsert=True # upsert=True means "insert if not found"
    )
# ---------------------------------

# Routes
@app.route('/')
def index():
    if 'user_phone' not in session:
        return redirect(url_for('login_page'))
    return render_template('index.html')

@app.route('/signup.html')
def signup_page():
    return render_template('signup.html')

@app.route('/signup', methods=['POST'])
def signup():
    phone = request.form['phone']
    password = request.form['password']
    
    # UPDATED: Check if user exists in the DB
    if users_collection.find_one({"phone": phone}):
        flash('Phone number already registered.')
        return redirect(url_for('signup_page'))
    
    # UPDATED: Insert new user into the DB
    users_collection.insert_one({
        "phone": phone,
        "hash": generate_password_hash(password)
    })
    
    flash('Account created! Please log in.')
    return redirect(url_for('login_page'))

@app.route('/login.html')
def login_page():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    phone = request.form['phone']
    password = request.form['password']
    
    # UPDATED: Find user in the DB
    user = users_collection.find_one({"phone": phone})
    
    # UPDATED: Check hash from the DB
    if user and check_password_hash(user["hash"], password):
        session['user_phone'] = phone
        return redirect(url_for('index'))
    
    flash('Invalid phone or password.')
    return redirect(url_for('login_page'))

@app.route('/logout')
def logout():
    session.pop('user_phone', None)
    return redirect(url_for('login_page'))

@app.route('/competitions.html')
def competitions_page():
    if 'user_phone' not in session:
        return redirect(url_for('login_page'))
    return render_template('competitions.html')

@app.route('/api/competitions')
def get_competitions():
    # This function now reads from the database!
    return jsonify(load_competitions())

@app.route('/admin.html')
@auth_required
def admin_page():
    return render_template('admin.html')

@app.route('/admin/competitions', methods=['GET', 'POST'])
@auth_required
def manage_competitions():
    competitions = load_competitions()
    if request.method == 'POST':
        data = request.json
        # Note: This ID logic is still fragile, but we'll leave it for now
        comp_id = str(len([c for cat in competitions for sub in competitions[cat] for c in competitions[cat][sub]]) + 1)
        new_comp = {
            'id': comp_id,
            'name': data['name'],
            'description': data.get('description', ''),
            'date': data.get('date', ''),
            'location': data.get('location', ''),
            'participant_limit': data.get('participant_limit', ''),
            'entry_fee': data.get('entry_fee', ''),
            'prizes': data.get('prizes', ''),
            'link': data.get('link', ''),
            'image': data.get('image', '')
        }
        category = data['category'].lower()
        subcategory = data['subcategory'].lower()
        if category not in competitions:
            competitions[category] = {}
        if subcategory not in competitions[category]:
            competitions[category][subcategory] = []
        competitions[category][subcategory].append(new_comp)
        
        # UPDATED: Save to database
        save_competitions(competitions)
        
        return jsonify({'id': comp_id, 'message': 'Competition added'}), 201
    return jsonify(competitions)

@app.route('/admin/competitions/<id>', methods=['PUT', 'DELETE'])
@auth_required
def update_or_delete_competition(id):
    competitions = load_competitions()
    for category in competitions:
        for subcategory in competitions[category]:
            for comp in competitions[category][subcategory]:
                if comp['id'] == id:
                    if request.method == 'PUT':
                        data = request.json
                        comp.update({
                            'name': data.get('name', comp['name']),
                            'description': data.get('description', comp['description']),
                            'date': data.get('date', comp['date']),
                            'location': data.get('location', comp['location']),
                            'participant_limit': data.get('participant_limit', comp['participant_limit']),
                            'entry_fee': data.get('entry_fee', comp['entry_fee']),
                            'prizes': data.get('prizes', comp['prizes']),
                            'link': data.get('link', comp['link']),
                            'image': data.get('image', comp['image'])
                        })
                        
                        # UPDATED: Save to database
                        save_competitions(competitions)
                        return jsonify({'message': 'Competition updated'})
                    
                    elif request.method == 'DELETE':
                        competitions[category][subcategory].remove(comp)
                        if not competitions[category][subcategory]:
                            del competitions[category][subcategory]
                        if not competitions[category]:
                            del competitions[category]
                        
                        # UPDATED: Save to database
                        save_competitions(competitions)
                        return jsonify({'message': 'Competition deleted'})
    return jsonify({'error': 'Competition not found'}), 404

if __name__ == '__main__':
    app.run(debug=True, port=5000)