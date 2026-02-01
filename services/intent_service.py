import json
from db import faq_collection

INTENTS_PATH = "data/intents.json"

def generate_intents_from_db():
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
        json.dump({"intents": intents}, f, indent=2, ensure_ascii=False)

    print("✅ intents.json updated from MongoDB")