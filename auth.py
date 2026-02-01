from functools import wraps
from flask import redirect, session, jsonify

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("user"):
            return redirect("/admin/login")
        return f(*args, **kwargs)
    return wrapper

def superadmin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("user"):
            return jsonify({"error": "Unauthorized"}), 401
        if session["user"]["role"] != "superadmin":
            return jsonify({"error": "Forbidden"}), 403
        return f(*args, **kwargs)
    return wrapper

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = session.get("user")
        if not user:
            return jsonify({"error": "Unauthorized"}), 403

        if user.get("role") not in ["admin", "superadmin"]:
            return jsonify({"error": "Forbidden"}), 403

        return f(*args, **kwargs)
    return decorated