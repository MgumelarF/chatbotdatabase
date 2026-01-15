# modellain.py
# Chatbot Kelurahan - Semantic Matching + Dialog Management Ringan
# Fokus: ringan, aman, dan tahan pertanyaan warga yang random

import json
import os
import random
import pickle
import hashlib
import numpy as np

from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

# =========================
# KONFIGURASI
# =========================
INTENTS_FILE = "intents.json"
CACHE_FILE = "intent_cache.pkl"
HASH_FILE = "intent_hash.txt"

EMBED_MODEL = "paraphrase-MiniLM-L6-v2"
SIMILARITY_THRESHOLD = 0.45
TOP_K = 2

# intent yang bukan layanan utama
NON_LAYANAN = {
    "salam",
    "selamat_tinggal",
    "terima_kasih"
}

# =========================
# UTIL HASH FILE
# =========================
def file_hash(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

# =========================
# LOAD INTENTS
# =========================
if not os.path.exists(INTENTS_FILE):
    raise FileNotFoundError("intents.json tidak ditemukan")

with open(INTENTS_FILE, encoding="utf-8") as f:
    intents = json.load(f)

print("⚙️ Memuat model bahasa...")
embedder = SentenceTransformer(EMBED_MODEL)

# =========================
# CACHE EMBEDDING
# =========================
def load_cache():
    if not os.path.exists(CACHE_FILE) or not os.path.exists(HASH_FILE):
        return None

    if open(HASH_FILE).read().strip() != file_hash(INTENTS_FILE):
        return None

    try:
        with open(CACHE_FILE, "rb") as f:
            return pickle.load(f)
    except:
        return None

def save_cache(data):
    with open(CACHE_FILE, "wb") as f:
        pickle.dump(data, f)
    with open(HASH_FILE, "w") as f:
        f.write(file_hash(INTENTS_FILE))

intent_data = load_cache()

if intent_data is None:
    print("🔄 Membuat embedding intent...")
    intent_data = []

    for intent in intents["intents"]:
        patterns = intent.get("patterns", [])
        if patterns:
            embeddings = embedder.encode(patterns, convert_to_numpy=True)
        else:
            embeddings = np.zeros((1, embedder.get_sentence_embedding_dimension()))

        intent_data.append({
            "tag": intent["tag"],
            "responses": intent.get("responses", []),
            "embeddings": embeddings
        })

    save_cache(intent_data)
else:
    print("✅ Cache intent digunakan")

print("🤖 Chatbot siap digunakan")

# =========================
# HELPER
# =========================
def is_confirmation(text):
    text = text.lower().strip()
    return text in ["iya", "ya", "betul", "benar", "oke", "ok"]

def get_response(tag):
    for intent in intents["intents"]:
        if intent["tag"] == tag:
            return random.choice(intent.get("responses", []))

    for intent in intents["intents"]:
        if intent["tag"] == "fallback":
            return random.choice(intent.get("responses", []))

    return "Maaf, saya belum memahami pertanyaan Anda."

# =========================
# PREDIKSI MULTI INTENT
# =========================
def predict_intents(text, top_k=TOP_K):
    if not text.strip():
        return []

    user_vec = embedder.encode([text], convert_to_numpy=True)[0]
    results = []

    for item in intent_data:
        if item["tag"] in NON_LAYANAN:
            continue

        sims = cosine_similarity([user_vec], item["embeddings"])[0]
        score = float(np.max(sims))

        if score >= SIMILARITY_THRESHOLD:
            results.append({
                "tag": item["tag"],
                "score": score
            })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]

# =========================
# FUNGSI UTAMA UNTUK WEB
# =========================
def chat(user_text, state):
    """
    state = {
        "awaiting_confirmation": bool,
        "last_options": []
    }
    """

    # keluar
    if user_text.lower() in ["exit", "keluar", "quit"]:
        return "Terima kasih telah menghubungi kelurahan 🙏", state

    # =====================
    # JAWAB KONFIRMASI
    # =====================
    if state.get("awaiting_confirmation") and is_confirmation(user_text):
        replies = []
        for tag in state.get("last_options", []):
            replies.append(get_response(tag))

        state["awaiting_confirmation"] = False
        state["last_options"] = []

        return "\n\n".join(replies), state

    # =====================
    # PREDIKSI INTENT
    # =====================
    results = predict_intents(user_text)

    if not results:
        return get_response("fallback"), state

    # =====================
    # SATU INTENT
    # =====================
    if len(results) == 1:
        return get_response(results[0]["tag"]), state

    # =====================
    # MULTI / AMBIGU
    # =====================
    gap = results[0]["score"] - results[1]["score"]

    if gap < 0.1:
        tags = [r["tag"] for r in results]

        state["awaiting_confirmation"] = True
        state["last_options"] = tags

        opsi = " dan ".join(tag.replace("_", " ") for tag in tags)

        return (
            "Saya menemukan lebih dari satu layanan yang mungkin.\n"
            f"Apakah yang Anda maksud adalah {opsi}?",
            state
        )

    return get_response(results[0]["tag"]), state
