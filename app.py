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
from modellain import predict_intent_semantic, get_response

# =========================
# INIT APP
# =========================
app = Flask(__name__)
app.secret_key = "admin-secret"

# CORS (AMAN UNTUK CHATBOT)
CORS(app)

# =========================
# PATH FILE
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

FAQ_FILE = os.path.join(BASE_DIR, "faq.json")
INTENTS_FILE = os.path.join(BASE_DIR, "intents.json")
NEW_PY_FILE = os.path.join(BASE_DIR, "new.py")

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

    if (
        data.get("username") == "admin"
        and data.get("password") == "admin123"
    ):
        session["admin"] = True
        return jsonify({"success": True})

    return jsonify({"success": False})


# =========================
# FAQ API (BUKAN CHATBOT)
# =========================
@app.route("/faq")
def get_faq():
    if not os.path.exists(FAQ_FILE):
        return jsonify([])

    with open(FAQ_FILE, "r", encoding="utf-8") as f:
        return jsonify(json.load(f))


@app.route("/faq/update", methods=["POST"])
def update_faq():
    if not session.get("admin"):
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json(force=True)

    with open(FAQ_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return jsonify({"success": True})


# =========================
# INTENTS CHATBOT (ADMIN)
# =========================
@app.route("/intents")
def get_intents():
    if not session.get("admin"):
        return jsonify({"error": "Unauthorized"}), 403

    with open(INTENTS_FILE, "r", encoding="utf-8") as f:
        return jsonify({"content": f.read()})


@app.route("/intents/update", methods=["POST"])
def update_intents():
    if not session.get("admin"):
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json(force=True)
    content = data.get("content")

    with open(INTENTS_FILE, "w", encoding="utf-8") as f:
        f.write(content)

    # TRAIN ULANG MODEL
    subprocess.run(
        ["python", NEW_PY_FILE],
        cwd=BASE_DIR
    )

    return jsonify({"success": True})


# =========================
# CHATBOT API (INI YANG PENTING)
# =========================
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True)

    if not data or "message" not in data:
        return jsonify({
            "error": "Message kosong"
        }), 400

    user_text = data["message"]

    try:
        intent_tag, score = predict_intent_semantic(
            user_text,
            return_score=True
        )

        response = get_response(intent_tag)

        return jsonify({
            "intent": intent_tag,
            "confidence": round(float(score), 3),
            "response": response
        })

    except Exception as e:
        return jsonify({
            "error": "Chatbot error",
            "detail": str(e)
        }), 500


# =========================
# STATIC FILE (CSS / JS)
# =========================
@app.route("/<path:filename>")
def serve_files(filename):
    return send_from_directory(BASE_DIR, filename)


# =========================
# RUN SERVER
# =========================
if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
