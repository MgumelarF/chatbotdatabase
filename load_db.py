from db import db  # ambil instance MongoDB dari db.py
import json
import os

# Path file JSON
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CATEGORIES_FILE = os.path.join(BASE_DIR, "categories.json")
FAQ_FILE = os.path.join(BASE_DIR, "categories.json")  # ini kalau FAQ masih ikut categories.json
# Kalau ada faq.json berbeda, ganti pathnya ke faq.json
# FAQ_FILE = os.path.join(BASE_DIR, "faq.json")

# Load categories.json
with open(CATEGORIES_FILE, "r", encoding="utf-8") as f:
    categories_data = json.load(f)

categories_collection = db["categories"]
categories_collection.delete_many({})  # hapus data lama (opsional)
categories_collection.insert_many(categories_data)
print(f"{len(categories_data)} kategori berhasil dimasukkan ke database!")

# Load faq.json / categories.json
with open(FAQ_FILE, "r", encoding="utf-8") as f:
    faq_data = json.load(f)

faq_collection = db["faq"]
faq_collection.delete_many({})  # hapus data lama (opsional)
faq_collection.insert_many(faq_data)
print(f"{len(faq_data)} FAQ berhasil dimasukkan ke database!")