# modellain.py
# ChatBot Bahasa Indonesia — Semantic Matching (Sentence Transformers)
# Fitur:
# - Tidak menggunakan BoW/words.pkl/classes.pkl
# - Paham typo & variasi kalimat (semantic similarity)
# - Caching embeddings agar startup lebih cepat jika intents.json tidak berubah
# - Mudah diintegrasikan ke API (fungsi predict_intent_semantic & get_response)

import json
import os
import random
import hashlib
import pickle
import numpy as np
import nltk
from sklearn.metrics.pairwise import cosine_similarity

# Sentence transformer
from sentence_transformers import SentenceTransformer

# Pastikan nltk tokenizer tersedia
nltk.download('punkt', quiet=True)

# ---------- Konfigurasi ----------
INTENTS_FILE = "intents.json"
CACHE_FILE = "intent_data.pkl"
HASH_FILE = "intents.hash"
EMBED_MODEL_NAME = "paraphrase-MiniLM-L6-v2"  # ringan & cepat
SIMILARITY_THRESHOLD = 0.45  # sesuaikan: 0.3-0.5 (lebih rendah = lebih toleran)

# ---------- Util: file hash ----------
def get_file_hash(filename: str) -> str:
    h = hashlib.md5()
    with open(filename, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

# ---------- Load intents ----------
print("🔄 Memuat intents.json ...")
if not os.path.exists(INTENTS_FILE):
    print(f"❌ File {INTENTS_FILE} tidak ditemukan. Letakkan intents.json di folder yang sama.")
    raise SystemExit(1)

with open(INTENTS_FILE, encoding="utf-8") as f:
    intents = json.load(f)

# ---------- Inisialisasi model embedding ----------
print(f"⚙️ Memuat model embedding ({EMBED_MODEL_NAME}) — ini butuh koneksi internet jika belum terunduh.")
embedder = SentenceTransformer(EMBED_MODEL_NAME)

# ---------- Caching: kalau intents.json belum berubah, pakai cache ----------
def load_cached_intent_data():
    if not os.path.exists(CACHE_FILE) or not os.path.exists(HASH_FILE):
        return None
    try:
        old_hash = open(HASH_FILE).read().strip()
        new_hash = get_file_hash(INTENTS_FILE)
        if old_hash != new_hash:
            return None
        with open(CACHE_FILE, "rb") as f:
            data = pickle.load(f)
        # pastikan struktur data valid
        if isinstance(data, list) and len(data) > 0 and "tag" in data[0]:
            print("✅ Memuat intent embeddings dari cache.")
            return data
    except Exception as e:
        print("⚠️ Gagal memuat cache:", e)
    return None

def save_cached_intent_data(data):
    try:
        with open(CACHE_FILE, "wb") as f:
            pickle.dump(data, f)
        with open(HASH_FILE, "w") as f:
            f.write(get_file_hash(INTENTS_FILE))
        print("✅ Menyimpan cache intent embeddings.")
    except Exception as e:
        print("⚠️ Gagal menyimpan cache:", e)

intent_data = load_cached_intent_data()

# ---------- Jika cache tidak ada / berubah, buat embedding baru ----------
if intent_data is None:
    print("⚙️ Membuat embeddings untuk semua patterns di intents.json ...")
    intent_data = []
    for intent in intents.get("intents", []):
        patterns = intent.get("patterns", [])
        if not patterns:
            # sediakan embedding kosong agar struktur konsisten
            embeddings = np.zeros((1, embedder.get_sentence_embedding_dimension()))
        else:
            embeddings = embedder.encode(patterns, convert_to_numpy=True, show_progress_bar=False)
        intent_data.append({
            "tag": intent.get("tag"),
            "responses": intent.get("responses", []),
            "patterns": patterns,
            "embeddings": embeddings  # shape: (num_patterns, dim)
        })
    # simpan cache
    save_cached_intent_data(intent_data)

print("✅ Siap. ChatBot semantic aktif!\n")

# ---------- Fungsi prediksi (bisa di-import oleh API) ----------
def predict_intent_semantic(text: str, return_score: bool = False):
    """
    Prediksi tag intent berdasar similarity antara user text dan setiap pattern.
    Mengembalikan tag intent terbaik. Jika score terbaik < SIMILARITY_THRESHOLD, kembalikan 'fallback' (jika ada).
    Jika return_score True, mengembalikan (tag, score).
    """
    if not text or not text.strip():
        return ("fallback", 0.0) if return_score else "fallback"

    user_emb = embedder.encode([text], convert_to_numpy=True)[0]  # shape (dim,)
    best_tag = "fallback"
    best_score = 0.0

    for item in intent_data:
        emb = item["embeddings"]  # shape (n_patterns, dim)
        if emb is None or emb.size == 0:
            continue
        sims = cosine_similarity([user_emb], emb)[0]  # similarities to each pattern
        score = float(np.max(sims))
        if score > best_score:
            best_score = score
            best_tag = item["tag"]

    if best_score < SIMILARITY_THRESHOLD:
        best_tag = "fallback"

    if return_score:
        return best_tag, best_score
    return best_tag

def get_response(intent_tag: str, user_text: str = None):
    """
    Ambil response acak dari intents.json berdasarkan tag.
    Jika tag = 'fallback' dan terdapat intent 'fallback' di intents.json, gunakan response-nya.
    Jika tidak ada, gunakan pesan default.
    """
    for intent in intents.get("intents", []):
        if intent.get("tag") == intent_tag:
            responses = intent.get("responses", [])
            if responses:
                return random.choice(responses)
    # jika tidak ditemukan tag
    # cari fallback intent
    for intent in intents.get("intents", []):
        if intent.get("tag") == "fallback":
            responses = intent.get("responses", [])
            if responses:
                return random.choice(responses)
    # default fallback
    return "Maaf, aku belum paham maksudmu 😅"

# ---------- Interactive loop (CLI) ----------
if __name__ == "__main__":
    print("💬 Ketik pesan (ketik 'keluar' / 'exit' untuk berhenti)")
    while True:
        try:
            user = input("Kamu: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nBot: Sampai jumpa lagi! 👋")
            break

        if user.lower() in ["keluar", "exit", "quit"]:
            print("Bot: Sampai jumpa lagi! 👋")
            break
        if user == "":
            print("Bot: Silakan ketik sesuatu.")
            continue

        tag, score = predict_intent_semantic(user, return_score=True)
        response = get_response(tag, user)
        # tampilkan debug score kecil (bisa dihapus)
        # print(f"[debug] intent={tag} score={score:.3f}")
        print("Bot:", response)