import pymongo
import os
from dotenv import load_dotenv
import bcrypt

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
client = None
db = None
users_collection = None

def connect_db():
    global client, db, users_collection
    try:
        if MONGO_URL is None:
            raise ValueError("MONGO_URL not found in environment variables.")
        client = pymongo.MongoClient(MONGO_URL)
        db = client.project_cost_estimator_db 
        users_collection = db.users
        # Test connection
        client.admin.command('ping')
        print("Successfully connected to MongoDB!")
        return users_collection
    except pymongo.errors.ConfigurationError as e:
        print(f"MongoDB Configuration Error: {e}")
        print("Please ensure MONGO_URL is correct and your IP is whitelisted if necessary.")
        return None
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        return None

def get_users_collection():
    global users_collection
    if users_collection is None:
        return connect_db()
    return users_collection

def create_user(username, password):
    collection = get_users_collection()
    if collection is None:
        return False, "Database connection failed."
    if collection.find_one({"username": username}):
        return False, "Username already exists."
    
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    collection.insert_one({"username": username, "password": hashed_password})
    return True, "User created successfully."

def check_user(username, password):
    collection = get_users_collection()
    if collection is None:
        return False
    user = collection.find_one({"username": username})
    if user and bcrypt.checkpw(password.encode('utf-8'), user["password"]):
        return True
    return False

# Initialize connection when module is loaded
if users_collection is None:
    connect_db()