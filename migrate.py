import json
from pymongo import MongoClient
import os

# --- IMPORTANT ---
# PASTE YOUR FULL CONNECTION STRING (WITH PASSWORD) HERE
MONGO_URI = "mongodb+srv://shamiohaque556_db_user:1lKNDU9sZVQoZK7B@cluster0.qurad1z.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0" 
# ---------------

# Your local files
USERS_FILE = 'users.json'
COMPETITIONS_FILE = 'competitions.json'

print("Connecting to database...")
client = MongoClient(MONGO_URI)
db = client.ueldo_db
users_collection = db.users
data_collection = db.data
print("Connection successful.")

# --- Migrate Users ---
print(f"Loading {USERS_FILE}...")
if os.path.exists(USERS_FILE):
    with open(USERS_FILE, 'r') as f:
        users_data = json.load(f)
    
    print(f"Found {len(users_data)} users. Migrating...")
    count = 0
    for phone, hash_val in users_data.items():
        # Check if user already exists
        if not users_collection.find_one({"phone": phone}):
            users_collection.insert_one({"phone": phone, "hash": hash_val})
            count += 1
    print(f"Migrated {count} new users.")
else:
    print(f"No {USERS_FILE} found. Skipping users.")

# --- Migrate Competitions ---
print(f"Loading {COMPETITIONS_FILE}...")
if os.path.exists(COMPETITIONS_FILE):
    with open(COMPETITIONS_FILE, 'r') as f:
        competitions_data = json.load(f)
    
    print("Migrating competitions data...")
    # Save the entire JSON structure as one document
    data_collection.replace_one(
        {"_id": "competitions"},
        competitions_data,
        upsert=True
    )
    print("Competitions data migrated.")
else:
    print(f"No {COMPETITIONS_FILE} found. Skipping competitions.")

print("\n--- MIGRATION COMPLETE ---")
print("You can now delete this 'migrate.py' file if you want.")