import os
import csv
import logging
import firebase_admin
from firebase_admin import credentials, auth
from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel, EmailStr
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# --- 1. CONFIGURATION & LOGGING ---
app = FastAPI(title="Secure Management API", version="2.0.0")
logging.basicConfig(level=logging.INFO)

# MongoDB Setup
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(MONGO_URI)
db = client[os.getenv("MONGO_DB", "company_db")]
users_collection = db["users"]

# Firebase Setup
# Expects a path to serviceAccountKey.json in .env or a default path
cred_path = os.getenv("FIREBASE_CRED_PATH", "serviceAccountKey.json")
try:
    if os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        logging.info("✅ Firebase Admin Initialized")
    else:
        logging.warning("⚠️ Firebase Key not found. Auth will fail.")
except Exception as e:
    logging.error(f"Firebase Init Error: {e}")

# --- 2. SECURITY DEPENDENCY ---
def verify_token(authorization: str = Header(None)):
    """
    Verifies the Bearer Token sent by the frontend/client.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    token = authorization.split("Bearer ")[-1]
    
    try:
        # Verify token with Firebase
        decoded_token = auth.verify_id_token(token)
        return decoded_token  # Returns user dict (uid, email, etc.)
    except Exception as e:
        logging.error(f"Auth failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")

# --- 3. DATA MODELS ---
class User(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str = "Staff"

# --- 4. ENDPOINTS ---

@app.get("/users")
def get_all_users():
    """Fetch users from MongoDB (Primary)"""
    users = list(users_collection.find({}, {"_id": 0}))
    return users

@app.post("/users/onboard")
def onboard_user(user: User):
    """Adds user to MongoDB and triggers automation hooks (simulated)"""
    if users_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="User email already exists")

    user_entry = user.dict()
    user_entry["created_at"] = datetime.now().isoformat()
    
    # Insert into MongoDB
    users_collection.insert_one(user_entry)
    
    logging.info(f"🆕 User added: {user.email}")
    return {"status": "success", "message": "User onboarded to MongoDB."}

@app.delete("/users/{user_id}")
def delete_user(user_id: int, current_user: dict = Depends(verify_token)):
    """
    SECURE ENDPOINT: Only allows deletion if a valid Firebase Token is present.
    """
    logging.info(f"User {current_user['email']} is deleting user {user_id}")
    
    result = users_collection.delete_one({"id": user_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
        
    return {"status": "success", "message": f"User {user_id} deleted successfully."}