from typing import Tuple
from flask import Flask, request, jsonify, Response

from Reset_Password.email_service import send_verification_code, verify_otp
from User_Authentication.user_auth import UserAuthentication

app = Flask(__name__)

DATABASE_PATH = "physics_revision_app.db"
auth = UserAuthentication(DATABASE_PATH)


@app.route("/send_verification_code", methods=["POST"])
def handle_send_verification_code() -> Tuple[Response, int]:
    email = request.json.get("email")
    if not email:
        return jsonify({"error": "Email is required"}), 400
    return send_verification_code(email)


@app.route("/verify_otp", methods=["POST"])
def handle_verify_otp() -> Tuple[Response, int]:
    email = request.json.get("email")
    otp = request.json.get("otp")
    if not email or not otp:
        return jsonify({"error": "Email and OTP are required"}), 400
    return verify_otp(email, otp)


@app.route("/register", methods=["POST"])
def register_user() -> Tuple[Response, int]:
    data = request.json
    email = data.get("email")
    username = data.get("username")
    password = data.get("password")
    if not email or not username or not password:
        return jsonify({"error": "Email, username, and password are required"}), 400
    if auth.is_email_taken(email):
        return jsonify({"error": "Email is already taken"}), 409
    if auth.is_username_taken(username):
        return jsonify({"error": "Username is already taken"}), 409
    auth.insert_user_into_db(email, username, password)
    return jsonify({"message": "User registered successfully"}), 201


@app.route("/login", methods=["POST"])
def login_user() -> Tuple[Response, int]:
    data = request.json
    email_username = data.get("email_username")
    password = data.get("password")
    if not email_username or not password:
        return jsonify({"error": "Email/Username and password are required"}), 400
    success, error = auth.confirm_user_details(email_username, password)
    if success:
        return jsonify({"message": "Login successful"}), 200
    return jsonify({"error": error}), 401


@app.route("/update_password", methods=["POST"])
def update_password() -> Tuple[Response, int]:
    data = request.json
    email = data.get("email")
    new_password = data.get("password")
    if not email or not new_password:
        return jsonify({"error": "Email and new password are required"}), 400
    if auth.update_password(email, new_password):
        return jsonify({"message": "Password updated successfully"}), 200
    return jsonify({"error": "Failed to update password"}), 500


@app.route("/is_email_taken", methods=["GET"])
def check_email_taken() -> Tuple[Response, int]:
    email = request.args.get("email")
    if not email:
        return jsonify({"error": "Email is required"}), 400
    if auth.is_email_taken(email):
        return jsonify({"email_taken": True}), 200
    return jsonify({"email_taken": False}), 200


@app.route("/is_username_taken", methods=["GET"])
def check_username_taken() -> Tuple[Response, int]:
    username = request.args.get("username")
    if not username:
        return jsonify({"error": "Username is required"}), 400
    if auth.is_username_taken(username):
        return jsonify({"username_taken": True}), 200
    return jsonify({"username_taken": False}), 200


if __name__ == "__main__":
    app.run(debug=True)
