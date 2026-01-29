from dotenv import load_dotenv
import os
# Di bagian imports
from email_service import send_activation_email

load_dotenv()

from flask import (
    Flask,
    request,
    jsonify,
    redirect,
    session,
    send_from_directory,
    
)
import secrets
import json
import os
import re

from time import time
import time

try:
    from db import users_collection, admin_logs_collection, faq_collection, categories_collection, db
    print("✅ Database modules imported successfully")
except ImportError as e:
    print(f"⚠️ Database import error: {e}")
    # Buat dummy collections
    users_collection = None
    admin_logs_collection = None
    faq_collection = None
    categories_collection = None
    db = None
    
from werkzeug.security import generate_password_hash, check_password_hash
from auth import login_required, superadmin_required
from datetime import timedelta
from flask_cors import CORS

from chatbot_engine import get_response

from db import faq_collection, categories_collection
from services.intent_service import generate_intents_from_db
from utils.reload_model import refresh_chatbot

from datetime import datetime
from bson import ObjectId
from bson.objectid import ObjectId
from db import users_collection, admin_logs_collection


# ========== ANTI BRUTE FORCE LOGIN =============
from time import time

# =========================
# IMPORT CHATBOT ENGINE
# =========================
from chatbot_engine import get_response

# ========ALLOWED IPS==========
ALLOWED_IPS = ["127.0.0.1"]

def ip_protected():
    return request.remote_addr in ALLOWED_IPS

# ========== ANTI BRUTE FORCE LOGIN =============
login_attempts = {}

def too_many_attempts(ip):
    now = time()
    attempts = login_attempts.get(ip, [])
    attempts = [t for t in attempts if now - t < 60]  # 1 menit
    attempts.append(now)
    login_attempts[ip] = attempts
    return len(attempts) > 5

# Gunakan environment variables dengan fallback
SECRET_KEY = os.environ.get("SECRET_KEY", secrets.token_urlsafe(32))
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")

# Disable debug di production
DEBUG = os.environ.get("DEBUG", "False").lower() == "true"

# =========================
# INIT APP
# =========================
app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config['SESSION_COOKIE_SECURE'] = not DEBUG  # HTTPS only in production
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# ========== TIMEDELTA ==================
app.permanent_session_lifetime = timedelta(minutes=30)

# =========================
# STATE CHATBOT (WAJIB)
# =========================
chat_state = {
    "awaiting_confirmation": False,
    "last_options": []
}

# =========================
# PATH FILE
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

FAQ_FILE = os.path.join(BASE_DIR, "faq.json")
INTENTS_FILE = os.path.join(BASE_DIR, "intents.json")
CATEGORIES_FILE = os.path.join(BASE_DIR, "categories.json")

# =========================
# HELPER JSON
# =========================
def safe_load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# =========================
# LOG ADMIN ACTION
# =======================
def log_admin_action(action, detail):
    try:
        if not session.get("user"):
            print("LOG GAGAL: Tidak ada session")
            return

        admin_logs_collection.insert_one({
            "username": session["user"]["username"],
            "role": session["user"]["role"],
            "action": action,
            "detail": detail,
            "ip": request.remote_addr,
            "timestamp": datetime.utcnow()
        })
    except Exception as e:
        print("LOG ERROR:", e)

# =========================
# ROUTE HALAMAN
# =========================
@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")

@app.route("/admin/login")
def admin_login_page():
    if session.get("user"):
        return redirect("/dashboard")
    return send_from_directory(BASE_DIR, "login.html")

@app.route("/dashboard")
@login_required
def dashboard():
    return send_from_directory(BASE_DIR, "dashboard.html")

@app.route("/logout")
def logout():
    log_admin_action("LOGOUT", "User logout")
    session.clear()
    return redirect("/")

# =========================
# LOGIN API
# =========================
@app.route("/admin/login", methods=["POST"])
def admin_login_api():
    ip = request.remote_addr

    # CEK BRUTE FORCE
    if too_many_attempts(ip):
        return jsonify({
            "error": "Terlalu banyak percobaan login. Coba lagi 1 menit."
        }), 429

    data = request.get_json(force=True)
    username = data.get("username")
    password = data.get("password")

    user = users_collection.find_one({"username": username})

    if user and user.get("status") == "active" and check_password_hash(user["password"], password):
        session["user"] = {
            "id": str(user["_id"]),
            "username": user["username"],
            "role": user["role"],
        }

        # ➕ Tambahan activity log
        log_admin_action(
            "LOGIN",
            "Login berhasil"
        )

        return jsonify({"success": True})

    return jsonify({"success": False}), 401

# =========================
# FAQ API
# =========================
@app.route("/faq", methods=["GET"])
def get_faq():
    data = list(faq_collection.find({}))
    for f in data:
        f["_id"] = str(f["_id"])
    return jsonify(data)

@app.route("/faq", methods=["POST"])
def add_faq():
    if not session.get("user"):
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json(force=True)
    question = data.get("question", "").strip()
    answer = data.get("answer", "").strip()
    category_id = data.get("category_id")

    if not question or not answer:
        return jsonify({"error": "Question dan answer wajib"}), 400

    faq_collection.insert_one({
        "question": question,
        "answer": answer,
        "category_id": category_id
    })

    log_admin_action("ADD_FAQ", f"Menambahkan FAQ: {question}")

    # 🔥 Sinkronisasi AI
    generate_intents_from_db()
    refresh_chatbot()

    return jsonify({"success": True})

@app.route("/faq/<id>", methods=["PUT"])
def edit_faq(id):
    if not session.get("user"):
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json(force=True)

    faq_collection.update_one(
        {"_id": ObjectId(id)},
        {"$set": {
            "question": data.get("question"),
            "answer": data.get("answer"),
            "category_id": data.get("category_id")
        }}
    )

    log_admin_action("EDIT_FAQ", f"Edit FAQ ID {id}")

    generate_intents_from_db()
    refresh_chatbot()

    return jsonify({"success": True})

@app.route("/faq/<id>", methods=["DELETE"])
def delete_faq(id):
    if not session.get("user"):
        return jsonify({"error": "Unauthorized"}), 403

    faq = faq_collection.find_one({"_id": ObjectId(id)})

    faq_collection.delete_one({"_id": ObjectId(id)})

    if faq:
        log_admin_action("DELETE_FAQ", f"Hapus FAQ: {faq['question']}")

    generate_intents_from_db()
    refresh_chatbot()

    return jsonify({"success": True})



# =========================
# CATEGORY API (MONGODB)
# =========================
@app.route("/categories", methods=["GET"])
def get_categories():
    data = list(categories_collection.find({}))
    for c in data:
        c["_id"] = str(c["_id"])
    return jsonify(data)

@app.route("/categories", methods=["POST"])
def add_category():
    if not session.get("user"):
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json(force=True)
    name = data.get("name", "").strip()

    if not name:
        return jsonify({"error": "Nama kategori kosong"}), 400

    categories_collection.insert_one({"name": name})

    log_admin_action("ADD_CATEGORY", f"Tambah kategori: {name}")

    return jsonify({"success": True})


@app.route("/categories/<id>", methods=["PUT"])
def edit_category(id):
    if not session.get("user"):
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json(force=True)

    categories_collection.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"name": data.get("name")}}
    )

    log_admin_action("EDIT_CATEGORY", f"Edit kategori ID {id}")

    return jsonify({"success": True})

@app.route("/categories/<id>", methods=["DELETE"])
def delete_category(id):
    if not session.get("user"):
        return jsonify({"error": "Unauthorized"}), 403

    cat = categories_collection.find_one({"_id": ObjectId(id)})

    categories_collection.delete_one({"_id": ObjectId(id)})

    if cat:
        log_admin_action("DELETE_CATEGORY", f"Hapus kategori: {cat['name']}")

    return jsonify({"success": True})

# =========================
# INTENTS API (DYNAMIC RELOAD)
# =========================
@app.route("/intents")
def get_intents():
    if not session.get("user"):
        return jsonify({"error": "Unauthorized"}), 403

    if not os.path.exists(INTENTS_FILE):
        return jsonify({"content": ""})

    with open(INTENTS_FILE, "r", encoding="utf-8") as f:
        return jsonify({"content": f.read()})

@app.route("/intents/update", methods=["POST"])
def update_intents():
    if not session.get("user"):
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json(force=True)
    content = data.get("content")

    if not content:
        return jsonify({"error": "Konten kosong"}), 400

    try:
        with open(INTENTS_FILE, "w", encoding="utf-8") as f:
            f.write(content)

        reload_intents()

        log_admin_action(
            "UPDATE_INTENTS",
            "Memperbarui file intents.json"
        )

        return jsonify({
            "success": True,
            "message": "Intents diperbarui & chatbot langsung aktif"
        })

    except Exception as e:
        log_admin_action(
            "UPDATE_INTENTS_FAILED",
            f"Gagal update intents: {str(e)}"
        )
        return jsonify({"error": "Gagal update intents"}), 500


# =========================
# CHATBOT API
# =========================
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True)

    if not data or "message" not in data:
        return jsonify({"error": "Message kosong"}), 400

    try:
        user_message = data["message"]
        bot_reply = get_response(user_message)

        return jsonify({
            "response": bot_reply
        })

    except Exception as e:
        return jsonify({
            "error": "Chatbot error",
            "detail": str(e)
        }), 500

# =========================
# STATIC FILES
# =========================

@app.route("/static/<path:filename>")
def serve_static(filename):
    return send_from_directory(os.path.join(BASE_DIR, "static"), filename)

# ==========================
def create_default_admin():
    if users_collection.count_documents({}) == 0:
        users_collection.insert_one({
            "username": "owner",
            "password": generate_password_hash("Owner123!"),
            "role": "superadmin",
             "status": "active"
        })
        print("Superadmin dibuat: owner / Owner123!")

# ========================
# ADD ADMIN WITH EMAIL
# ========================

@app.route("/admin/users/add", methods=["POST"])
@superadmin_required
def add_admin_with_email():
    data = request.get_json()
    username = data.get("username", "").strip()
    email = data.get("email", "").strip()
    role = data.get("role", "admin")

    # === VALIDASI ===
    if not username or not email:
        return jsonify({"error": "Username dan email wajib"}), 400

    if not re.match(r"^[a-zA-Z0-9_]{3,20}$", username):
        return jsonify({"error": "Username tidak valid (3-20 karakter, hanya huruf/angka/_)"}), 400

    if not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
        return jsonify({"error": "Email tidak valid"}), 400

    if users_collection.find_one({"username": username}):
        return jsonify({"error": "Username sudah digunakan"}), 400

    if users_collection.find_one({"email": email}):
        return jsonify({"error": "Email sudah terdaftar"}), 400

    # === CREATE TOKEN ===
    activation_token = secrets.token_urlsafe(32)
    expires_at = int(time.time()) + 300  # 5 menit

    # === SAVE TO DATABASE ===
    users_collection.insert_one({
        "username": username,
        "email": email,
        "role": role,
        "activation_token": activation_token,
        "activation_expires_at": expires_at,
        "status": "pending",
        "created_at": datetime.utcnow()
    })

    # === BUILD ACTIVATION LINK ===
    BASE_URL = os.environ.get("BASE_URL", "https://chatbotdatabase-production.up.railway.app")
    activation_link = f"{BASE_URL}/admin/activate?token={activation_token}"

    # === KIRIM EMAIL DENGAN RESEND ===
    try:
        email_result = send_activation_email(email, username, activation_link)
        
        if email_result.get("success"):
            if email_result.get("testing_mode"):
                log_admin_action("ADD_ADMIN", f"Menambahkan admin '{username}' ({email}) - TEST MODE")
                return jsonify({
                    "success": True,
                    "testing_mode": True,
                    "message": f"Admin '{username}' ditambahkan.",
                    "activation_link": activation_link,
                    "note": f"Email dikirim ke admin utama (testing mode). Berikan link ini ke {username}: {activation_link}"
                })
            else:
                log_admin_action("ADD_ADMIN", f"Menambahkan admin '{username}' ({email}) - Email terkirim")
                return jsonify({
                    "success": True,
                    "message": f"Admin '{username}' ditambahkan. Email aktivasi dikirim ke {email}"
                })
        else:
            # Fallback jika email gagal
            log_admin_action("ADD_ADMIN", f"Menambahkan admin '{username}' ({email}) - Email GAGAL")
            return jsonify({
                "success": True,
                "message": f"Admin '{username}' ditambahkan. Email gagal dikirim.",
                "activation_link": activation_link,
                "note": "Berikan link ini ke user untuk aktivasi manual"
            })
            
    except Exception as e:
        # Jika ada error dalam proses email
        log_admin_action("ADD_ADMIN_ERROR", f"Error saat menambah admin: {str(e)}")
        return jsonify({
            "success": True,  # Admin tetap berhasil ditambahkan ke DB
            "message": f"Admin '{username}' ditambahkan ke database.",
            "activation_link": activation_link,
            "error": f"Email tidak terkirim: {str(e)}",
            "note": "Gunakan link di atas untuk aktivasi manual"
        })

# =========================
# activate admin account
# ========================
@app.route("/admin/activate", methods=["GET", "POST"])
def activate_admin():
    token = request.args.get("token")
    
    if not token:
        return "Token tidak ditemukan", 400

    user = users_collection.find_one({
        "activation_token": token,
        "status": "pending"
    })

    if not user:
        return "Token tidak valid atau sudah digunakan", 400

    expires_at = user.get("activation_expires_at")
    
    if expires_at and time.time() > expires_at:
        return "Token sudah kadaluarsa (lebih dari 5 menit)", 400
    
    if request.method == "POST":
        password = request.form.get("password")
        confirm = request.form.get("confirm_password")
        
        if not password or not confirm:
            return "Password dan konfirmasi wajib diisi", 400
            
        if password != confirm:
            return "Password tidak cocok", 400
            
        if len(password) < 6:
            return "Password minimal 6 karakter", 400

        # Update user
        users_collection.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "password": generate_password_hash(password),
                    "status": "active",
                    "updated_at": datetime.utcnow()
                },
                "$unset": {
                    "activation_token": "",
                    "activation_expires_at": ""
                }
            }
        )
        
        log_admin_action("ACTIVATE_ACCOUNT", f"Akun {user['username']} diaktifkan")
        
        return """
        <h2 style="color: green;">✅ Akun Berhasil Diaktifkan!</h2>
        <p>Password Anda telah dibuat. Sekarang Anda bisa login.</p>
        <p><a href="/admin/login">Klik di sini untuk login</a></p>
        """
    
    # GET request → tampilkan form HTML
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Aktivasi Akun</title>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 40px; max-width: 500px; margin: auto; }}
            input {{ width: 100%; padding: 10px; margin: 10px 0; }}
            button {{ background: #4CAF50; color: white; padding: 12px; border: none; width: 100%; cursor: pointer; }}
        </style>
    </head>
    <body>
        <h2>Buat Password untuk {user['username']}</h2>
        <form method='post'>
            <input type='password' name='password' placeholder='Password baru' required>
            <input type='password' name='confirm_password' placeholder='Konfirmasi password' required>
            <button type='submit'>Aktivasi Akun</button>
        </form>
    </body>
    </html>
    """

# ========== endpoint ==========
@app.route("/me")
def me():
    if not session.get("user"):
        return jsonify({"logged_in": False})
    return jsonify({"logged_in": True, "user": session["user"]})

# =========================
@app.route("/test-db")
def test_db():
    count = users_collection.count_documents({})
    return {"status": "connected", "users": count}

# ============================
def require_superadmin():
    if not session.get("user"):
        return False
    return session["user"]["role"] == "superadmin"

# ==========================
@app.route("/admin/users")
@superadmin_required
def list_users():
    if not require_superadmin():
        return jsonify({"error": "Forbidden"}), 403

    users = list(users_collection.find({}, {"password": 0}))
    for u in users:
        u["_id"] = str(u["_id"])

    return jsonify(users)

# ===================================
# DELETE USER ADMIN
# ===================================
@app.route("/admin/users/<id>", methods=["DELETE"])
def delete_user(id):
    if not require_superadmin():
        return jsonify({"error": "Forbidden"}), 403

    # 1. Ambil data user dulu (untuk log)
    user = users_collection.find_one({"_id": ObjectId(id)})

    # 2. Hapus user
    users_collection.delete_one({"_id": ObjectId(id)})

    # 3. Simpan log jika user ditemukan
    if user:
        log_admin_action(
            "DELETE_ADMIN",
            f"Menghapus admin '{user['username']}'"
        )

    return jsonify({"success": True})

# ========================
# ADMIN LOGS
# ========================
@app.route("/admin/logs")
@superadmin_required
def get_logs():
    logs = list(admin_logs_collection.find().sort("timestamp", -1).limit(200))

    for l in logs:
        l["_id"] = str(l["_id"])

    return jsonify(logs)

@app.route("/debug-email")
def debug_email():
    """Test email configuration"""
    resend_key = os.environ.get("RESEND_API_KEY")
    base_url = os.environ.get("BASE_URL")
    
    return jsonify({
        "RESEND_API_KEY_set": bool(resend_key),
        "RESEND_API_key_length": len(resend_key) if resend_key else 0,
        "BASE_URL": base_url,
        "testing_email": "fajafi217@gmail.com"
    })

# =========================
# INIT FILE & RUN
# =========================
if __name__ == "__main__":
    create_default_admin()
    for path in [FAQ_FILE, CATEGORIES_FILE]:
        if not os.path.exists(path):
            save_json(path, [])

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))