from flask import Flask, request, jsonify
from flask_cors import CORS

# IMPORT MODEL CHATBOT
from modellain import predict_intent_semantic, get_response

app = Flask(__name__)

# IZINKAN AKSES DARI HTML / JS
CORS(app, resources={r"/*": {"origins": "*"}})

# =========================
# ROUTE CHATBOT
# =========================
@app.route("/chat", methods=["POST"])
def chat():
    # Ambil data JSON dari frontend
    data = request.get_json(force=True)

    if not data or "message" not in data:
        return jsonify({
            "error": "Message tidak ditemukan"
        }), 400

    user_text = data["message"]

    try:
        # Prediksi intent + confidence
        intent_tag, score = predict_intent_semantic(
            user_text,
            return_score=True
        )

        # Ambil respon chatbot
        response = get_response(intent_tag)

        return jsonify({
            "intent": intent_tag,
            "confidence": round(float(score), 3),
            "response": response
        })

    except Exception as e:
        # Error handling supaya tidak crash
        return jsonify({
            "error": "Terjadi kesalahan pada server chatbot",
            "detail": str(e)
        }), 500


# =========================
# TEST SERVER (OPTIONAL)
# =========================
@app.route("/")
def health_check():
    return jsonify({
        "status": "API Chatbot aktif",
        "endpoint": "/chat"
    })


# =========================
# JALANKAN SERVER
# =========================
if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
