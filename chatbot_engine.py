from pymongo import MongoClient
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import os
import time
import re

# =========================
# CONFIG - GUNAKAN ENVIRONMENT VARIABLES
# =========================
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.environ.get("DB_NAME", "faq_app")
FAQ_COLLECTION = "faq"

# =========================
# HYPERPARAMETER CHATBOT (sama seperti model pertama)
# =========================
SIMILARITY_THRESHOLD = 0.38  # Threshold yang sama dengan model pertama
MULTI_INTENT_GAP = 0.08      # Gap yang sama
MAX_ANSWERS = 2              # Maksimal jawaban yang sama

# =========================
# KEYWORDS UNTUK PENYESUAIAN SCORE (sama seperti model pertama)
# =========================
KEYWORD_BARU = ["baru", "bikin", "pertama"]
KEYWORD_CETAK_ULANG = ["hilang", "rusak", "cetak ulang"]

# =========================
# GLOBAL VARIABLES
# =========================
client = None
db = None
faq_collection = None

# =========================
# CONNECT DB DENGAN RETRY LOGIC
# =========================
def connect_to_mongo():
    """
    Connect to MongoDB - langsung gunakan client dari db.py
    """
    global client, db, faq_collection
    
    try:
        # Import client dari db.py jika tersedia
        from db import client as db_client
        client = db_client
        
        # Test connection
        client.admin.command('ping')
        print("✅ Connected to MongoDB from chatbot_engine")
        
    except ImportError:
        # Jika db.py tidak ada, buat koneksi baru
        print("⚠️ db.py not found, creating new MongoDB connection...")
        try:
            client = MongoClient(
                MONGO_URI,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                socketTimeoutMS=30000,
                tls=False  # Nonaktifkan TLS untuk lokal
            )
            client.admin.command('ping')
            print("✅ New MongoDB connection created")
        except Exception as e:
            print(f"❌ New connection failed: {e}")
            client = None
    
    # Setup database dan collection
    if client:
        try:
            db = client[DB_NAME]
            faq_collection = db[FAQ_COLLECTION]
            print(f"✅ Database '{DB_NAME}' and collection '{FAQ_COLLECTION}' ready")
        except Exception as e:
            print(f"❌ Failed to setup database: {e}")
    else:
        # Buat dummy client untuk offline mode
        print("⚠️ Using dummy MongoDB client (offline mode)")
        class DummyMongoClient:
            def __getitem__(self, name):
                class DummyCollection:
                    def find(self, *args, **kwargs):
                        return []
                    def find_one(self, *args, **kwargs):
                        return None
                    def insert_one(self, *args, **kwargs):
                        return type('obj', (object,), {'inserted_id': 'dummy_id'})
                    def update_one(self, *args, **kwargs):
                        return type('obj', (object,), {'matched_count': 0})
                    def delete_one(self, *args, **kwargs):
                        return type('obj', (object,), {'deleted_count': 0})
                    def count_documents(self, *args, **kwargs):
                        return 0
                return DummyCollection()
        
        client = DummyMongoClient()
        db = client[DB_NAME]
        faq_collection = db[FAQ_COLLECTION]
    
    return client

# Panggil fungsi koneksi saat module di-load
connect_to_mongo()

# =========================
# LOAD MODEL - TF-IDF RINGAN
# =========================
print("⚙️ Loading TF-IDF model...")

# Preprocessing function sederhana
def preprocess_text(text):
    if not text:
        return ""
    # Lowercase
    text = text.lower()
    # Remove extra whitespace
    text = ' '.join(text.split())
    return text

# TF-IDF Vectorizer yang ringan
vectorizer = TfidfVectorizer(
    lowercase=False,  # Already lowercase in preprocessing
    stop_words=None,  # Tidak pakai stop words agar lebih akurat
    ngram_range=(1, 2),  # Bisa single word atau 2 kata
    min_df=1,  # Minimal 1 dokumen
    max_features=1000  # Batasi features untuk lebih ringan
)

print("✅ TF-IDF ready")

# =========================
# LOAD FAQ
# =========================
faq_data = []
faq_embeddings = None

def load_faq():
    global faq_data, faq_embeddings
    print("📥 Loading FAQ from MongoDB...")
    
    try:
        faq_data = list(faq_collection.find({}))
    except Exception as e:
        print(f"❌ Failed to load FAQ from collection: {e}")
        faq_data = []

    if not faq_data:
        faq_embeddings = None
        print("⚠️ FAQ kosong")
        # Tambahkan data dummy untuk testing jika kosong
        faq_data = [
            {"_id": "1", "question": "cara buat ktp", "answer": "Untuk membuat KTP baru, bawa KK asli, surat pengantar RT/RW, dan fotokopi akta kelahiran ke kelurahan.", "category_id": "ktp"},
            {"_id": "2", "question": "syarat ktp baru", "answer": "Syarat KTP baru: KK asli, surat pengantar RT/RW, fotokopi akta kelahiran, pas foto ukuran 3x4.", "category_id": "ktp"},
            {"_id": "3", "question": "cetak ulang ktp", "answer": "Untuk cetak ulang KTP yang hilang/rusak: bawa KK asli, surat kehilangan dari kepolisian, dan bayar biaya administrasi.", "category_id": "ktp"}
        ]
        print("✅ Using dummy FAQ data for testing")

    # Preprocess questions
    questions = [preprocess_text(f["question"]) for f in faq_data]
    
    try:
        # Fit and transform FAQ questions
        faq_embeddings = vectorizer.fit_transform(questions).toarray()
        print(f"✅ {len(faq_data)} FAQ loaded and vectorized")
        
    except Exception as e:
        print(f"❌ Failed to encode FAQ: {e}")
        faq_embeddings = None

# Load FAQ on startup
load_faq()

# =========================
# HELPER: KEYWORD SCORE - SAMA PERSIS DENGAN MODEL PERTAMA
# =========================
def keyword_adjustment(user_text, faq_question):
    u = user_text.lower()
    q = faq_question.lower()
    score = 0.0

    if any(k in u for k in KEYWORD_BARU):
        if "baru" in q:
            score += 0.05
        if "cetak ulang" in q or "hilang" in q:
            score -= 0.10

    if any(k in u for k in KEYWORD_CETAK_ULANG):
        if "cetak ulang" in q or "hilang" in q:
            score += 0.05
        if "baru" in q:
            score -= 0.10

    return score

# =========================
# CHAT FUNCTION - SAMA PERSIS LOGIKANYA DENGAN MODEL PERTAMA
# =========================
def get_response(user_text: str) -> str:
    if not user_text.strip():
        return "Silakan ketik pertanyaan Anda."

    if faq_embeddings is None or len(faq_data) == 0:
        return "Data FAQ belum tersedia. Coba lagi nanti."

    try:
        # Preprocess user input
        processed_input = preprocess_text(user_text)
        
        # Transform user input to vector
        user_vec = vectorizer.transform([processed_input]).toarray()[0]
        
        # Calculate similarities
        sims = cosine_similarity([user_vec], faq_embeddings)[0]
        
        # Debug info (opsional)
        print(f"📊 Max similarity: {max(sims):.3f}")
        
        # Apply threshold and keyword adjustment - LOGIKA SAMA
        scored = []
        for idx, base_score in enumerate(sims):
            if base_score < SIMILARITY_THRESHOLD:
                continue

            adjust = keyword_adjustment(user_text, faq_data[idx]["question"])
            final_score = base_score + adjust
            scored.append((idx, final_score))

        if not scored:
            return "Maaf, saya belum menemukan jawaban yang sesuai.\n\nCoba tanya tentang:\n• Cara membuat KTP\n• Syarat KTP baru\n• Cetak ulang KTP\n• Layanan kelurahan"

        # Sort by score
        scored.sort(key=lambda x: x[1], reverse=True)

        # Get top answer(s) - LOGIKA SAMA
        best_score = scored[0][1]
        selected = [
            (idx, score)
            for idx, score in scored
            if score >= best_score - MULTI_INTENT_GAP
        ][:MAX_ANSWERS]

        # Format response
        responses = []
        for idx, _ in selected:
            responses.append(f"📌 {faq_data[idx]['answer']}")

        return "\n\n".join(responses)
    
    except Exception as e:
        print(f"❌ Chatbot error: {e}")
        return "Maaf, terjadi kesalahan dalam memproses pertanyaan Anda."

# =========================
# RELOAD FUNCTION - SAMA
# =========================
def reload_chatbot():
    print("🔄 Reload chatbot...")
    load_faq()
    print("✅ Reload selesai")

# =========================
# UTILITY FUNCTIONS
# =========================
def get_faq_stats():
    """Get FAQ statistics"""
    if not faq_data:
        return {"count": 0, "status": "empty"}
    
    return {
        "count": len(faq_data),
        "status": "loaded",
        "categories": len(set(f.get("category_id", "") for f in faq_data))
    }

# Test the chatbot on load
if __name__ == "__main__":
    print("🧪 Testing chatbot...")
    test_questions = [
        "Halo",
        "Bagaimana cara membuat KTP?",
        "Syarat buat KTP"
    ]
    
    for question in test_questions:
        print(f"\nQ: {question}")
        response = get_response(question)
        print(f"A: {response}")