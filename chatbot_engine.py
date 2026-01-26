from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import os  # <-- TAMBAHKAN INI
import logging  # <-- TAMBAHKAN INI

# =========================
# CONFIG
# =========================
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")  # <-- GANTI INI
DB_NAME = "faq_app"
FAQ_COLLECTION = "faq"

SIMILARITY_THRESHOLD = 0.38
MULTI_INTENT_GAP = 0.08
MAX_ANSWERS = 2

# Keyword logic
KEYWORD_BARU = ["baru", "bikin", "pertama"]
KEYWORD_CETAK_ULANG = ["hilang", "rusak", "cetak ulang"]

# =========================
# CONNECT DB
# =========================
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)  # <-- TAMBAHKAN timeout
    client.admin.command('ping')  # <-- TAMBAHKAN ping test
    print("✅ MongoDB connected successfully")
except Exception as e:
    print(f"❌ MongoDB connection failed: {e}")
    raise e

db = client[DB_NAME]
faq_collection = db[FAQ_COLLECTION]

# =========================
# LOAD MODEL (DENGAN ERROR HANDLING)
# =========================
print("⚙️ Loading embedding model...")

try:
    # Coba download model jika belum ada
    model_name = "paraphrase-MiniLM-L6-v2"
    embedder = SentenceTransformer(model_name)
    print(f"✅ Model {model_name} loaded successfully")
except Exception as e:
    print(f"❌ Failed to load model: {e}")
    # Fallback simple model
    class SimpleEmbedder:
        def encode(self, texts, **kwargs):
            # Return dummy embeddings
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