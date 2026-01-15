from flask import (
    Flask,
    request,
    jsonify,
    redirect,
    session,
    send_from_directory
)
from flask_cors import CORS
import json
import os
import subprocess

# =========================
# IMPORT MODEL CHATBOT
# =========================
from modellain import chat as chatbot_engine

# =========================
# INIT APP
# =========================
app = Flask(__name__)
app.secret_key = "admin-secret"

# =========================
# STATE CHATBOT (WAJIB)
# =========================
chat_state = {
    "awaiting_confirmation": False,
    "last_options": []
}

# CORS (AMAN UNTUK CHATBOT)
CORS(app)

# =========================
# PATH FILE
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

FAQ_FILE = os.path.join(BASE_DIR, "faq.json")
INTENTS_FILE = os.path.join(BASE_DIR, "intents.json")
CATEGORIES_FILE = os.path.join(BASE_DIR, "categories.json")
NEW_PY_FILE = os.path.join(BASE_DIR, "new.py")

# =========================
# HELPER LOAD FILE JSON AMAN
# =========================
def safe_load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data
    except (json.JSONDecodeError, FileNotFoundError):
        return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# =========================
# ROUTE HALAMAN
# =========================
@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")

@app.route("/login", methods=["GET"])
def login_page():
    return send_from_directory(BASE_DIR, "login.html")

@app.route("/dashboard")
def dashboard():
    if not session.get("admin"):
        return redirect("/login")
    return send_from_directory(BASE_DIR, "dashboard.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# =========================
# LOGIN API
# =========================
@app.route("/login", methods=["POST"])
def login_api():
    data = request.get_json(force=True)
    if data.get("username") == "admin" and data.get("password") == "admin123":
        session["admin"] = True
        return jsonify({"success": True})
    return jsonify({"success": False})

# =========================
# FAQ API
# =========================
@app.route("/faq")
def get_faq():
    faqs = safe_load_json(FAQ_FILE, [])
    return jsonify(faqs)

@app.route("/faq/update", methods=["POST"])
def update_faq():
    if not session.get("admin"):
        return jsonify({"error": "Unauthorized"}), 403
    data = request.get_json(force=True)
    save_json(FAQ_FILE, data)
    return jsonify({"success": True})

# =========================
# CATEGORIES API
# =========================
@app.route("/categories", methods=["GET"])
def get_categories():
    categories = safe_load_json(CATEGORIES_FILE, [])
    return jsonify(categories)

@app.route("/categories", methods=["POST"])
def add_category():
    if not session.get("admin"):
        return jsonify({"error": "Unauthorized"}), 403
    data = request.get_json(force=True)
    name = data.get("name")
    if not name:
        return jsonify({"error": "Nama kategori kosong"}), 400

    categories = safe_load_json(CATEGORIES_FILE, [])
    # generate id
    new_id = max([c.get("id", 0) for c in categories], default=0) + 1
    categories.append({"id": new_id, "name": name})
    save_json(CATEGORIES_FILE, categories)
    return jsonify({"success": True, "id": new_id})

@app.route("/categories/<int:cat_id>", methods=["PUT"])
def edit_category(cat_id):
    if not session.get("admin"):
        return jsonify({"error": "Unauthorized"}), 403
    data = request.get_json(force=True)
    name = data.get("name")
    if not name:
        return jsonify({"error": "Nama kategori kosong"}), 400

    categories = safe_load_json(CATEGORIES_FILE, [])
    for cat in categories:
        if cat["id"] == cat_id:
            cat["name"] = name
            save_json(CATEGORIES_FILE, categories)
            return jsonify({"success": True})
    return jsonify({"error": "Kategori tidak ditemukan"}), 404

@app.route("/categories/<int:cat_id>", methods=["DELETE"])
def delete_category(cat_id):
    if not session.get("admin"):
        return jsonify({"error": "Unauthorized"}), 403
    categories = safe_load_json(CATEGORIES_FILE, [])
    categories = [c for c in categories if c["id"] != cat_id]
    save_json(CATEGORIES_FILE, categories)
    return jsonify({"success": True})

# =========================
# INTENTS CHATBOT
# =========================
@app.route("/intents")
def get_intents():
    if not session.get("admin"):
        return jsonify({"error": "Unauthorized"}), 403
    content = ""
    if os.path.exists(INTENTS_FILE):
        with open(INTENTS_FILE, "r", encoding="utf-8") as f:
            content = f.read()
    return jsonify({"content": content})

@app.route("/intents/update", methods=["POST"])
def update_intents():
    if not session.get("admin"):
        return jsonify({"error": "Unauthorized"}), 403
    data = request.get_json(force=True)
    content = data.get("content")
    if content is not None:
        with open(INTENTS_FILE, "w", encoding="utf-8") as f:
            f.write(content)
        # TRAIN ULANG MODEL
        subprocess.run(["python", NEW_PY_FILE], cwd=BASE_DIR)
    return jsonify({"success": True})

# =========================
# CHATBOT API
# =========================
@app.route("/chat", methods=["POST"])
def chat():
    global chat_state

    data = request.get_json(force=True)
    if not data or "message" not in data:
        return jsonify({"error": "Message kosong"}), 400

    user_text = data["message"]

    try:
        response, chat_state = chatbot_engine(user_text, chat_state)

        return jsonify({
            "response": response
        })

    except Exception as e:
        return jsonify({
            "error": "Chatbot error",
            "detail": str(e)
        }), 500

# =========================
# STATIC FILES
# =========================
@app.route("/<path:filename>")
def serve_files(filename):
    return send_from_directory(BASE_DIR, filename)

# =========================
# RUN SERVER
# =========================
if __name__ == "__main__":
    # pastikan categories.json dan faq.json ada
    for file_path in [CATEGORIES_FILE, FAQ_FILE]:
        if not os.path.exists(file_path):
            save_json(file_path, [])
    app.run(host="0.0.0.0", port=5000, debug=True)
