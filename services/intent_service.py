# services/intent_service.py

import json
import os
from bson import ObjectId

# Tentukan path yang benar
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

# Buat folder data jika belum ada
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR, exist_ok=True)

INTENTS_PATH = os.path.join(DATA_DIR, "intents.json")

def generate_intents_from_db():
    """Generate intents.json from database FAQ"""
    try:
        from db import faq_collection, categories_collection
        
        # Ambil semua FAQ
        faqs = list(faq_collection.find({}))
        
        # Group FAQ by category
        intents_dict = {}
        
        for faq in faqs:
            category_id = faq.get("category_id")
            
            # Jika ada category_id, cari nama kategori
            if category_id:
                try:
                    category = categories_collection.find_one({"_id": ObjectId(category_id)})
                    category_name = category.get("name", "Uncategorized") if category else "Uncategorized"
                except:
                    category_name = "Uncategorized"
            else:
                category_name = "Uncategorized"
            
            # Tambahkan ke dictionary berdasarkan kategori
            if category_name not in intents_dict:
                intents_dict[category_name] = {
                    "tag": category_name,
                    "patterns": [],
                    "responses": []
                }
            
            # Tambahkan pattern dan response
            intents_dict[category_name]["patterns"].append(faq.get("question", ""))
            intents_dict[category_name]["responses"].append(faq.get("answer", ""))
        
        # Konversi ke format intents.json
        intents_list = list(intents_dict.values())
        
        # Buat struktur akhir
        intents_data = {
            "intents": intents_list
        }
        
        # Tulis ke file dengan error handling
        try:
            with open(INTENTS_PATH, "w", encoding="utf-8") as f:
                json.dump(intents_data, f, indent=2, ensure_ascii=False)
            print(f"✅ Intents berhasil diperbarui: {len(intents_list)} kategori")
            return True
        except Exception as e:
            print(f"❌ Gagal menulis file intents.json: {str(e)}")
            # Coba alternatif path
            alt_path = os.path.join(BASE_DIR, "intents.json")
            try:
                with open(alt_path, "w", encoding="utf-8") as f:
                    json.dump(intents_data, f, indent=2, ensure_ascii=False)
                print(f"✅ Intents berhasil disimpan di path alternatif: {alt_path}")
                return True
            except Exception as e2:
                print(f"❌ Gagal juga di path alternatif: {str(e2)}")
                return False
        
    except Exception as e:
        print(f"❌ Error generate_intents_from_db: {str(e)}")
        return False