from datetime import datetime
from typing import Tuple
from flask import Flask, request, jsonify, Response

from Flashcard_System.database_operations.database_service import DatabaseService
from Flashcard_System.fsrs_manager import FSRSManager
from Reset_Password.email_service import send_verification_code, verify_otp
from User_Authentication.user_auth import UserAuthentication

app = Flask(__name__)

DATABASE_PATH = "physics_revision_app.db"
auth = UserAuthentication(DATABASE_PATH)
fsrs_manager = FSRSManager(DATABASE_PATH)
db_service = DatabaseService("physics_revision_app.db")
today = datetime(2024, 11, 26)


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


@app.route("/get_user_id", methods=["GET"])
def get_user_id() -> Tuple[Response, int]:
    email_or_username = request.args.get("email_or_username")
    if not email_or_username:
        return jsonify({"error": "Email or username is required"}), 400

    user_id = auth.get_user_id(email_or_username)
    if user_id is not None:
        return jsonify({"user_id": user_id}), 200
    return jsonify({"error": "User not found"}), 404

@app.route("/get_username", methods=["GET"])
def get_username() -> Tuple[Response, int]:
    user_id = request.args.get("user_id", type=int)
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400
    username = auth.get_username(user_id)
    if username:
        return jsonify({"username": username}), 200
    return jsonify({"error": "User not found"}), 404

@app.route("/get_due_flashcards", methods=["GET"])
def get_due_flashcards():
    user_id = request.args.get("user_id", type=int)
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400
    try:
        # today = datetime(2024, 11, 19)
        flashcards = fsrs_manager.fetch_due_flashcards(user_id, today)
        return jsonify({"flashcards": flashcards}), 200
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/get_flashcards_by_set", methods=["GET"])
def get_flashcards_by_set():
    user_id = request.args.get("user_id", type=int)
    set_name = request.args.get("set_name", type=str)

    if not all([user_id, set_name]):
        return jsonify({"error": "User ID and set name are required"}), 400
    try:
        flashcards = db_service.flashcard_ops.fetch_flashcards_by_set(user_id, set_name)
        print(jsonify({"flashcards": flashcards}))
        return jsonify({"flashcards": flashcards}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/get_sets", methods=["GET"])
def get_sets():
    user_id = request.args.get("user_id", type=int)
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400
    try:
        sets = db_service.flashcard_ops.fetch_sets(user_id)
        return jsonify({"sets": sets}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/submit_rating", methods=["POST"])
def submit_rating():
    data = request.json
    user_id = data.get("user_id")
    card_id = data.get("card_id")
    rating = data.get("rating")

    if not all([user_id, card_id, rating]):
        return jsonify({"error": "User ID, card ID, and rating are required"}), 400
    # today = datetime(2024, 11, 19)
    success = fsrs_manager.process_rating(
        user_id,
        card_id,
        rating,
        today,
    )
    if success:
        return jsonify({"success": True}), 200
    else:
        return jsonify({"error": "Failed to process rating"}), 500

@app.route("/create_flashcard", methods=["POST"])
def create_flashcard():
    data = request.json

    user_id = data.get("user_id")
    flashcard_data = data.get("flashcard_data", {})
    set_name = flashcard_data.get("set_name")
    front = flashcard_data.get("front")
    back = flashcard_data.get("back")

    if not all([user_id, set_name, front, back]):
        return jsonify({"error": "User ID, set name, front, and back are required"}), 400

    try:
        # today = datetime(2024, 11, 26)
        card_id = db_service.flashcard_ops.create_flashcard(user_id, flashcard_data, today)
        return jsonify({"card_id": card_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
