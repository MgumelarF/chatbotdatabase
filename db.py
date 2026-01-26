import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    print("✅ MongoDB connected successfully")
except ConnectionFailure as e:
    print(f"❌ MongoDB connection failed: {e}")
    raise e

DB_NAME = os.environ.get("DB_NAME", "faq_app")
db = client[DB_NAME]

# Collections
users_collection = db["users"]
admin_logs_collection = db["admin_logs"]
faq_collection = db["faq"]
categories_collection = db["categories"]