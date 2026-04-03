#auth-service/app.py:
from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)

ROBLE_API_URL=os.getenv("ROBLE_API_URL", "https://roble-api.openlab.uninorte.edu.co/auth/ds2_fd1af67fb8")

# 🔐 --- LOGIN ---
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    try:
        res = requests.post(f"{ROBLE_API_URL}/login", json={
            "email": email,
            "password": password
        })
        return jsonify(res.json()), res.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 🧾 --- SIGNUP ---
@app.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    name = data.get("name")

    try:
        res = requests.post(f"{ROBLE_API_URL}/signup-direct", json={
            "email": email,
            "password": password,
            "name": name
        })
        return jsonify(res.json()), res.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 🔄 --- REFRESH TOKEN ---
@app.route("/refresh-token", methods=["POST"])
def refresh_token():
    data = request.get_json()
    refresh_token = data.get("refreshToken")

    try:
        res = requests.post(f"{ROBLE_API_URL}/refresh-token", json={
            "refreshToken": refresh_token
        })
        return jsonify(res.json()), res.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 🚪 --- LOGOUT ---
@app.route("/logout", methods=["POST"])
def logout():
    token = request.headers.get("Authorization")

    try:
        res = requests.post(f"{ROBLE_API_URL}/logout", headers={
            "Authorization": token
        })
        return jsonify(res.json()), res.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ✅ --- VERIFY TOKEN ---
@app.route("/verify-token", methods=["GET"])
def verify_token():
    token = request.headers.get("Authorization")

    try:
        res = requests.get(f"{ROBLE_API_URL}/verify-token", headers={
            "Authorization": token
        })
        return jsonify(res.json()), res.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)