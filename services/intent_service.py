import json
import os
from db import faq_collection

# 🔥 ambil base directory aplikasi
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

INTENTS_PATH = os.path.join(BASE_DIR, "data", "intents.json")

def generate_intents_from_db():
    # ✅ pastikan folder data ada
    os.makedirs(os.path.dirname(INTENTS_PATH), exist_ok=True)

    faq_data = list(faq_collection.find({}))

    intents = [
        {
            "tag": "salam",
            "patterns": ["halo", "hai", "assalamualaikum"],
            "responses": ["Halo! Ada yang bisa saya bantu?"]
        },
        {
            "tag": "fallback",
            "patterns": [],
            "responses": ["Maaf, saya belum memahami pertanyaan tersebut."]
        }
    ]

    for faq in faq_data:
        intents.append({
            "tag": f"faq_{faq['_id']}",
            "patterns": [faq["question"]],
            "responses": [faq["answer"]]
        })

    with open(INTENTS_PATH, "w", encoding="utf-8") as f:
        json.dump(
            {"intents": intents},
            f,
            indent=2,
            ensure_ascii=False
        )

    print("✅ intents.json updated at:", INTENTS_PATH)