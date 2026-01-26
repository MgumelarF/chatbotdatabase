from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import os
import time

# =========================
# CONFIG - GUNAKAN ENVIRONMENT VARIABLES
# =========================
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.environ.get("DB_NAME", "faq_app")
FAQ_COLLECTION = "faq"

# Jika MONGO_URI tidak ada, beri warning tapi jangan crash
if not MONGO_URI or MONGO_URI == "mongodb://localhost:27017/":
    print("⚠️ WARNING: MONGO_URI not set. Using localhost (may fail in Railway)")

print(f"🔗 Connecting to MongoDB: {MONGO_URI[:50]}...")

# =========================
# CONNECT DB DENGAN RETRY LOGIC
# =========================
def connect_to_mongo():
    max_retries = 3
    for attempt in range(max_retries):
        try:
            client = MongoClient(
                MONGO_URI,
                serverSelectionTimeoutMS=10000,
                connectTimeoutMS=10000,
                socketTimeoutMS=10000
            )
            # Test connection
            client.admin.command('ping')
            print("✅ MongoDB connected successfully")
            return client
        except Exception as e:
            print(f"❌ MongoDB connection attempt {attempt + 1}/{max_retries} failed: {str(e)[:100]}")
            if attempt < max_retries - 1:
                time.sleep(2)  # Tunggu 2 detik sebelum retry
            else:
                print("⚠️ WARNING: Could not connect to MongoDB. Some features may not work.")
                return None

client = connect_to_mongo()

# Jika koneksi gagal, buat dummy client untuk mencegah crash
if client is None:
    class DummyMongoClient:
        def __getitem__(self, name):
            class DummyCollection:
                def find(self, *args, **kwargs):
                    return []
                def find_one(self, *args, **kwargs):
                    return None
                def insert_one(self, *args, **kwargs):
                    return None
                def update_one(self, *args, **kwargs):
                    return None
                def delete_one(self, *args, **kwargs):
                    return None
                def count_documents(self, *args, **kwargs):
                    return 0
            return DummyCollection()
    
    db = DummyMongoClient()
    print("⚠️ Using dummy MongoDB client (offline mode)")
else:
    db = client[DB_NAME]

faq_collection = db[FAQ_COLLECTION]

# =========================
# LOAD MODEL (SAMA SEPERTI SEBELUMNYA)
# =========================
print("⚙️ Loading embedding model...")

try:
    model_name = "paraphrase-MiniLM-L6-v2"
    embedder = SentenceTransformer(model_name)
    print(f"✅ Model {model_name} loaded successfully")
except Exception as e:
    print(f"❌ Failed to load model: {e}")
    # Fallback simple model
    class SimpleEmbedder:
        def encode(self, texts, **kwargs):
            import numpy as np
            return np.random.randn(len(texts), 384)
    
    embedder = SimpleEmbedder()
    print("⚠️ Using dummy embedder - chatbot accuracy will be low")

# =========================
# LOAD FAQ
# =========================
faq_data = []
faq_embeddings = None

def load_faq():
    global faq_data, faq_embeddings
    print("📥 Loading FAQ from MongoDB...")

    faq_data = list(faq_collection.find({}))

    if not faq_data:
        faq_embeddings = None
        print("⚠️ FAQ kosong")
        return

    questions = [f["question"] for f in faq_data]
    
    try:
        faq_embeddings = embedder.encode(questions, convert_to_numpy=True)
        print(f"✅ {len(faq_data)} FAQ loaded")
    except Exception as e:
        print(f"❌ Failed to encode FAQ: {e}")
        faq_embeddings = None

load_faq()

# =========================
# HELPER: KEYWORD SCORE
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
# CHAT FUNCTION (DENGAN ERROR HANDLING)
# =========================
def get_response(user_text: str) -> str:
    if not user_text.strip():
        return "Silakan ketik pertanyaan Anda."

    if faq_embeddings is None:
        return "Data FAQ belum tersedia."

    try:
        user_vec = embedder.encode([user_text], convert_to_numpy=True)[0]
        sims = cosine_similarity([user_vec], faq_embeddings)[0]

        scored = []
        for idx, base_score in enumerate(sims):
            if base_score < SIMILARITY_THRESHOLD:
                continue

            adjust = keyword_adjustment(user_text, faq_data[idx]["question"])
            final_score = base_score + adjust
            scored.append((idx, final_score))

        if not scored:
            return "Maaf, saya belum menemukan jawaban yang sesuai."

        scored.sort(key=lambda x: x[1], reverse=True)

        best_score = scored[0][1]
        selected = [
            (idx, score)
            for idx, score in scored
            if score >= best_score - MULTI_INTENT_GAP
        ][:MAX_ANSWERS]

        responses = []
        for idx, _ in selected:
            responses.append(f"📌 {faq_data[idx]['answer']}")

        return "\n\n".join(responses)
    
    except Exception as e:
        print(f"❌ Chatbot error: {e}")
        return "Maaf, terjadi kesalahan dalam memproses pertanyaan Anda."

# =========================
# RELOAD
# =========================
def reload_chatbot():
    print("🔄 Reload chatbot...")
    load_faq()
    print("✅ Reload selesai")