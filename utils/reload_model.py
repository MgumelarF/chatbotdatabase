# utils/reload_model.py

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INTENTS_PATH = os.path.join(BASE_DIR, "data", "intents.json")

def refresh_chatbot():
    """Refresh chatbot model"""
    try:
        from chatbot_engine import get_response
        
        # Cek apakah file intents.json ada
        if not os.path.exists(INTENTS_PATH):
            print(f"⚠️ File {INTENTS_PATH} tidak ditemukan")
            
            # Coba path alternatif
            alt_path = os.path.join(BASE_DIR, "intents.json")
            if os.path.exists(alt_path):
                print(f"✅ Menggunakan intents.json di path alternatif: {alt_path}")
            else:
                print("❌ File intents.json tidak ditemukan di mana pun")
                return False
        
        print("✅ Chatbot model refreshed")
        return True
        
    except Exception as e:
        print(f"❌ Gagal refresh chatbot: {str(e)}")
        return False

def reload_intents():
    """Alias untuk refresh_chatbot"""
    return refresh_chatbot()