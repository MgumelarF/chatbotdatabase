import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv
import certifi

# Load .env (untuk lokal)
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise ValueError("❌ MONGO_URI belum diset di environment variable!")

try:
    client = MongoClient(
        MONGO_URI,
        tls=True,
        tlsCAFile=certifi.where(),
        serverSelectionTimeoutMS=5000
    )
    client.admin.command('ping')
    print("✅ MongoDB connected successfully")
except ConnectionFailure as e:
    print(f"❌ MongoDB connection failed: {e}")
    raise e

DB_NAME = os.getenv("DB_NAME", "faq_app")
db = client[DB_NAME]

# Collections
users_collection = db["users"]
admin_logs_collection = db["admin_logs"]
faq_collection = db["faq"]
categories_collection = db["categories"]

print("DB name:", db.name)
print("Collections:", db.list_collection_names())

docs = list(faq_collection.find())
print("Jumlah FAQ:", len(docs))

if docs:
    print("Contoh 1 data FAQ:", docs[0])
