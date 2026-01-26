# sync_faq.py
from pymongo import MongoClient
import json
import os

# ======= CONFIG =======
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = "faq_app"  # ganti sesuai db yang sudah ada

FAQ_FILE = "faq.json"
INTENTS_FILE = "intents.json"

# ======= CONNECT DB =======
client = MongoClient(MONGO_URI)
db = client[DB_NAME]

faq_collection = db["faq"]
categories_collection = db["categories"]  # opsional kalau mau cek kategori

# ======= LOAD FAQ JSON =======
with open(FAQ_FILE, "r", encoding="utf-8") as f:
    faq_data = json.load(f)

# ======= CLEAR EXISTING DATA =======
faq_collection.delete_many({})

# ======= INSERT FAQ =======
faq_collection.insert_many(faq_data)
print("FAQ berhasil dimasukkan ke database!")

# ======= GENERATE INTENTS.JSON =======
intents = []

# intents default
intents += [
    {
        "tag": "salam",
        "patterns": ["hai", "halo", "hello", "hei", "hey", "selamat pagi", "selamat siang", "selamat sore", "selamat malam", "assalamualaikum", "shalom", "namo buddhaya"],
        "responses": ["Halo! Ada yang bisa saya bantu?", "Hai, selamat datang di layanan Kelurahan Cipinang Melayu 😊", "Halo! Silakan sampaikan keperluan Anda."]
    },
    {
        "tag": "fallback",
        "patterns": [],
        "responses": ["Maaf, saya belum memahami pertanyaan tersebut 😅", "Bisa dijelaskan sedikit lebih detail?"]
    }
]

# Buat intents dari FAQ
for faq in faq_data:
    tag = f"faq_{faq['category_id']}_{faq_data.index(faq)}"
    intents.append({
        "tag": tag,
        "patterns": [faq["question"]],
        "responses": [faq["answer"]]
    })

# Simpan ke intents.json
with open(INTENTS_FILE, "w", encoding="utf-8") as f:
    json.dump({"intents": intents}, f, indent=2, ensure_ascii=False)

print("intents.json berhasil dibuat & disinkronkan dengan FAQ!")