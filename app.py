from datetime import datetime
import logging
from typing import Tuple
from flask import Flask, request, jsonify, Response

from Flashcard_System.database_operations.database_service import DatabaseService
from Flashcard_System.fsrs_manager import FSRSManager
from Reset_Password.email_service import send_verification_code, verify_otp
from User_Authentication.user_auth import UserAuthentication

# Configure logging
logging.basicConfig(
    filename="application.log",
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

DATABASE_PATH = "physics_revision_app.db"
auth = UserAuthentication(DATABASE_PATH)
fsrs_manager = FSRSManager(DATABASE_PATH)
db_service = DatabaseService("physics_revision_app.db")
# today = datetime(2024, 12, 3)
today = datetime.today()


@app.route("/send_verification_code", methods=["POST"])
def handle_send_verification_code() -> Tuple[Response, int]:
    email = request.json.get("email")
    if not email:
        logger.warning(f"Verification code request failed: No email provided")
        return jsonify({"error": "Email is required"}), 400
    logger.info(f"Verification code sent to {email}")
    return send_verification_code(email)


@app.route("/verify_otp", methods=["POST"])
def handle_verify_otp() -> Tuple[Response, int]:
    email = request.json.get("email")
    otp = request.json.get("otp")
    if not email or not otp:
        logger.warning(f"OTP verification failed: Missing email or OTP")
        return jsonify({"error": "Email and OTP are required"}), 400
    logger.info(f"OTP verification attempted for {email}")
    return verify_otp(email, otp)


@app.route("/register", methods=["POST"])
def register_user() -> Tuple[Response, int]:
    data = request.json
    email = data.get("email")
    username = data.get("username")
    password = data.get("password")
    if not email or not username or not password:
        logger.warning(f"Registration failed: Incomplete user details")
        return jsonify({"error": "Email, username, and password are required"}), 400
    if auth.is_email_taken(email):
        logger.warning(f"Registration failed: Email {email} already taken")
        return jsonify({"error": "Email is already taken"}), 409
    if auth.is_username_taken(username):
        logger.warning(f"Registration failed: Username {username} already taken")
        return jsonify({"error": "Username is already taken"}), 409
    auth.insert_user_into_db(email, username, password)
    logger.info(f"User registered successfully: {email}")
    return jsonify({"message": "User registered successfully"}), 201


@app.route("/login", methods=["POST"])
def login_user() -> Tuple[Response, int]:
    data = request.json
    email_username = data.get("email_username")
    password = data.get("password")
    if not email_username or not password:
        logger.warning(f"Login attempt failed: Missing credentials")
        return jsonify({"error": "Email/Username and password are required"}), 400
    success, error = auth.confirm_user_details(email_username, password)
    if success:
        logger.info(f"Successful login for {email_username}")
        return jsonify({"message": "Login successful"}), 200
    logger.warning(f"Login failed for {email_username}: {error}")
    return jsonify({"error": error}), 401


@app.route("/update_password", methods=["POST"])
def update_password() -> Tuple[Response, int]:
    data = request.json
    email = data.get("email")
    new_password = data.get("password")
    if not email or not new_password:
        logger.warning(f"Password update failed: Missing email or new password")
        return jsonify({"error": "Email and new password are required"}), 400
    if auth.update_password(email, new_password):
        logger.info(f"Password updated successfully for {email}")
        return jsonify({"message": "Password updated successfully"}), 200
    logger.error(f"Failed to update password for {email}")
    return jsonify({"error": "Failed to update password"}), 500


@app.route("/is_email_taken", methods=["GET"])
def check_email_taken() -> Tuple[Response, int]:
    email = request.args.get("email")
    if not email:
        logger.warning(f"Email check failed: No email provided")
        return jsonify({"error": "Email is required"}), 400
    is_taken = auth.is_email_taken(email)
    logger.info(f"Email {email} taken status: {is_taken}")
    if is_taken:
        return jsonify({"email_taken": True}), 200
    return jsonify({"email_taken": False}), 200


@app.route("/is_username_taken", methods=["GET"])
def check_username_taken() -> Tuple[Response, int]:
    username = request.args.get("username")
    if not username:
        logger.warning(f"Username check failed: No username provided")
        return jsonify({"error": "Username is required"}), 400
    is_taken = auth.is_username_taken(username)
    logger.info(f"Username {username} taken status: {is_taken}")
    if is_taken:
        return jsonify({"username_taken": True}), 200
    return jsonify({"username_taken": False}), 200


@app.route("/get_user_id", methods=["GET"])
def get_user_id() -> Tuple[Response, int]:
    email_or_username = request.args.get("email_or_username")
    if not email_or_username:
        logger.warning(f"User ID retrieval failed: No email/username provided")
        return jsonify({"error": "Email or username is required"}), 400

    user_id = auth.get_user_id(email_or_username)
    if user_id is not None:
        logger.info(f"Retrieved user ID for {email_or_username}")
        return jsonify({"user_id": user_id}), 200
    logger.warning(f"User not found: {email_or_username}")
    return jsonify({"error": "User not found"}), 404


@app.route("/get_username", methods=["GET"])
def get_username() -> Tuple[Response, int]:
    user_id = request.args.get("user_id", type=int)
    if not user_id:
        logger.warning(f"Username retrieval failed: No user ID provided")
        return jsonify({"error": "User ID is required"}), 400
    username = auth.get_username(user_id)
    if username:
        logger.info(f"Retrieved username for user ID {user_id}")
        return jsonify({"username": username}), 200
    logger.warning(f"Username not found for user ID {user_id}")
    return jsonify({"error": "User not found"}), 404


@app.route("/get_due_flashcards", methods=["GET"])
def get_due_flashcards():
    user_id = request.args.get("user_id", type=int)
    if not user_id:
        logger.warning(f"Due flashcards retrieval failed: No user ID provided")
        return jsonify({"error": "User ID is required"}), 400
    try:
        flashcards = fsrs_manager.fetch_due_flashcards(user_id, today)
        logger.info(f"Retrieved due flashcards for user ID {user_id}")
        return jsonify({"flashcards": flashcards}), 200
    except Exception as e:
        logger.error(f"Error retrieving due flashcards for user ID {user_id}: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/get_flashcards_by_set", methods=["GET"])
def get_flashcards_by_set():
    user_id = request.args.get("user_id", type=int)
    set_name = request.args.get("set_name", type=str)

    if not all([user_id, set_name]):
        logger.warning(
            f"Flashcards by set retrieval failed: Missing user ID or set name"
        )
        return jsonify({"error": "User ID and set name are required"}), 400
    try:
        flashcards = db_service.flashcard_ops.fetch_flashcards_by_set(user_id, set_name)
        logger.info(f"Retrieved flashcards for set {set_name} for user ID {user_id}")
        return jsonify({"flashcards": flashcards}), 200
    except Exception as e:
        logger.error(f"Error retrieving flashcards for set {set_name}: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/get_sets", methods=["GET"])
def get_sets():
    user_id = request.args.get("user_id", type=int)
    if not user_id:
        logger.warning(f"Sets retrieval failed: No user ID provided")
        return jsonify({"error": "User ID is required"}), 400
    try:
        sets = db_service.flashcard_ops.fetch_sets(user_id)
        logger.info(f"Retrieved sets for user ID {user_id}")
        return jsonify({"sets": sets}), 200
    except Exception as e:
        logger.error(f"Error retrieving sets for user ID {user_id}: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/submit_rating", methods=["POST"])
def submit_rating():
    data = request.json
    user_id = data.get("user_id")
    card_id = data.get("card_id")
    rating = data.get("rating")

    if not all([user_id, card_id, rating]):
        logger.warning(f"Rating submission failed: Missing user ID, card ID, or rating")
        return jsonify({"error": "User ID, card ID, and rating are required"}), 400
    success = fsrs_manager.process_rating(
        user_id,
        card_id,
        rating,
        today,
    )
    if success:
        logger.info(
            f"Rating submitted successfully for card ID {card_id} by user ID {user_id}"
        )
        return jsonify({"success": True}), 200
    else:
        logger.error(
            f"Failed to process rating for card ID {card_id} by user ID {user_id}"
        )
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
        logger.warning(f"Flashcard creation failed: Missing required fields")
        return (
            jsonify({"error": "User ID, set name, front, and back are required"}),
            400,
        )

    try:
        card_id = db_service.flashcard_ops.create_flashcard(
            user_id, flashcard_data, today
        )
        logger.info(
            f"Flashcard created successfully for user ID {user_id} in set {set_name}"
        )
        return jsonify({"card_id": card_id}), 201
    except Exception as e:
        logger.error(f"Error creating flashcard for user ID {user_id}: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/delete_card", methods=["POST"])
def delete_card():
    data = request.json
    user_id = data.get("user_id")
    card_id = data.get("card_id")
    if not all([user_id, card_id]):
        logger.warning(f"Card deletion failed: Missing user ID or card ID")
        return jsonify({"error": "User ID and card ID are required"}), 400
    try:
        db_service.flashcard_ops.delete_card(user_id, card_id)
        db_service.user_performance_ops.delete_card(user_id, card_id)
        logger.info(
            f"Flashcard deleted successfully for card ID {card_id} by user ID {user_id}"
        )
        return jsonify({"message": "Flashcard deleted successfully"}), 200
    except Exception as e:
        logger.error(f"Error deleting flashcard for card ID {card_id}: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/delete_set", methods=["POST"])
def delete_set():
    data = request.json
    user_id = data.get("user_id")
    set_name = data.get("set_name")
    if not all([user_id, set_name]):
        logger.warning(f"Set deletion failed: Missing user ID or set name")
        return jsonify({"error": "User ID and set name are required"}), 400
    try:
        card_id_to_delete = db_service.flashcard_ops.get_card_id_for_set(
            user_id, set_name
        )
        db_service.flashcard_ops.delete_set(user_id, set_name)
        db_service.user_performance_ops.delete_set(user_id, card_id_to_delete)
        logger.info(
            f"Flashcard set deleted successfully for user ID {user_id}: {set_name}"
        )
        return jsonify({"message": "Flashcard set deleted successfully"}), 200
    except Exception as e:
        logger.error(f"Error deleting set {set_name} for user ID {user_id}: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/update_flashcard", methods=["POST"])
def update_flashcard():
    data = request.json
    user_id = data.get("user_id")
    flashcard = data.get("flashcard")
    if not all([user_id, flashcard]):
        logger.warning(f"Flashcard update failed: Missing user ID or flashcard details")
        return jsonify({"error": "User ID, set name, and flashcard are required"}), 400
    try:
        db_service.flashcard_ops.update_flashcard(user_id, flashcard)
        logger.info(f"Flashcard updated successfully for user ID {user_id}")
        return jsonify({"message": "Flashcard updated successfully"}), 200
    except Exception as e:
        logger.error(f"Error updating flashcard for user ID {user_id}: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/get_review_log_by_month", methods=["GET"])
def get_review_log_by_month():
    user_id = request.args.get("user_id", type=int)
    month = request.args.get("month", type=str)
    year = request.args.get("year", type=int)
    if not all([user_id, month, year]):
        logger.warning(f"Review log retrieval failed: Missing user ID, month, or year")
        return jsonify({"error": "User ID, month, and year are required"}), 400
    try:
        review_log = db_service.daily_review_log_ops.get_review_log_by_month(
            user_id, month, year
        )
        logger.info(f"Retrieved review log for user ID {user_id} for {month} {year}")
        return jsonify({"review_log": review_log}), 200
    except Exception as e:
        logger.error(f"Error retrieving review log for user ID {user_id}: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/get_next_reviews_by_month", methods=["GET"])
def get_next_reviews_by_month():
    user_id = request.args.get("user_id", type=int)
    month = request.args.get("month", type=str)
    year = request.args.get("year", type=int)
    if not all([user_id, month, year]):
        logger.warning(
            f"Next reviews retrieval failed: Missing user ID, month, or year"
        )
        return jsonify({"error": "User ID, month, and year are required"}), 400
    try:
        next_reviews = db_service.user_performance_ops.get_next_reviews_by_month(
            user_id, month, year
        )
        logger.info(f"Retrieved next reviews for user ID {user_id} for {month} {year}")
        return jsonify({"next_reviews": next_reviews}), 200
    except Exception as e:
        logger.error(f"Error retrieving next reviews for user ID {user_id}: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/get_all_current_card_states", methods=["GET"])
def get_all_current_card_states():
    user_id = request.args.get("user_id", type=int)
    if not user_id:
        logger.warning(f"Card states retrieval failed: No user ID provided")
        return jsonify({"error": "User ID is required"}), 400
    try:
        card_states = db_service.user_performance_ops.get_all_current_card_states(
            user_id
        )
        logger.info(f"Retrieved all current card states for user ID {user_id}")
        return jsonify({"card_states": card_states}), 200
    except Exception as e:
        logger.error(f"Error retrieving card states for user ID {user_id}: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/get_total_lapses", methods=["GET"])
def get_total_lapses():
    user_id = request.args.get("user_id", type=int)
    if not user_id:
        logger.warning(f"Total lapses retrieval failed: No user ID provided")
        return jsonify({"error": "User ID is required"}), 400
    try:
        total_lapses = db_service.user_performance_ops.get_total_lapses(user_id)
        logger.info(f"Retrieved total lapses for user ID {user_id}: {total_lapses}")
        return jsonify({"total_lapses": total_lapses}), 200
    except Exception as e:
        logger.error(f"Error retrieving total lapses for user ID {user_id}: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/get_stability_data", methods=["GET"])
def get_stability_data():
    user_id = request.args.get("user_id", type=int)
    if not user_id:
        logger.warning(f"Stability data retrieval failed: No user ID provided")
        return jsonify({"error": "User ID is required"}), 400
    try:
        stability_data = db_service.user_performance_ops.get_stability_data(user_id)
        logger.info(f"Retrieved stability data for user ID {user_id}")
        return jsonify({"stability_data": stability_data}), 200
    except Exception as e:
        logger.error(f"Error retrieving stability data for user ID {user_id}: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/get_difficulty_data", methods=["GET"])
def get_difficulty_data():
    user_id = request.args.get("user_id", type=int)
    if not user_id:
        logger.warning(f"Difficulty data retrieval failed: No user ID provided")
        return jsonify({"error": "User ID is required"}), 400
    try:
        difficulty_data = db_service.user_performance_ops.get_difficulty_data(user_id)
        logger.info(f"Retrieved difficulty data for user ID {user_id}")
        return jsonify({"difficulty_data": difficulty_data}), 200
    except Exception as e:
        logger.error(f"Error retrieving difficulty data for user ID {user_id}: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/get_current_ratings", methods=["GET"])
def get_current_ratings():
    user_id = request.args.get("user_id", type=int)
    if not user_id:
        logger.warning(f"Current ratings retrieval failed: No user ID provided")
        return jsonify({"error": "User ID is required"}), 400
    try:
        current_ratings = db_service.user_performance_ops.get_current_ratings(user_id)
        logger.info(f"Retrieved current ratings for user ID {user_id}")
        return jsonify({"current_ratings": current_ratings}), 200
    except Exception as e:
        logger.error(f"Error retrieving current ratings for user ID {user_id}: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/update_email", methods=["POST"])
def update_email():
    data = request.json
    user_id = data.get("user_id")
    new_email = data.get("email")
    if not all([user_id, new_email]):
        logger.warning(f"Email update failed: Missing user ID or new email")
        return jsonify({"error": "User ID and new email are required"}), 400
    if auth.update_email(user_id, new_email):
        logger.info(f"Email updated successfully for user ID {user_id}")
        return jsonify({"message": "Email updated successfully"}), 200
    logger.error(f"Failed to update email for user ID {user_id}")
    return jsonify({"error": "Failed to update email"}), 500


@app.route("/update_username", methods=["POST"])
def update_username():
    data = request.json
    user_id = data.get("user_id")
    new_username = data.get("username")
    if not all([user_id, new_username]):
        logger.warning(f"Username update failed: Missing user ID or new username")
        return jsonify({"error": "User ID and new username are required"}), 400
    if auth.update_username(user_id, new_username):
        logger.info(f"Username updated successfully for user ID {user_id}")
        return jsonify({"message": "Username updated successfully"}), 200
    logger.error(f"Failed to update username for user ID {user_id}")
    return jsonify({"error": "Failed to update username"}), 500


@app.route("/update_daily_review_limit", methods=["POST"])
def update_daily_review_limit():
    data = request.json
    user_id = data.get("user_id")
    new_limit = data.get("new_limit")
    if not all([user_id, new_limit]):
        logger.warning(
            f"Daily review limit update failed: Missing user ID or new limit"
        )
        return jsonify({"error": "User ID and new limit are required"}), 400
    if db_service.user_settings_ops.update_daily_review_limit(user_id, new_limit):
        logger.info(f"Daily review limit updated to {new_limit} for user ID {user_id}")
        return jsonify({"message": "Daily review limit updated successfully"}), 200
    logger.error(f"Failed to update daily review limit for user ID {user_id}")
    return jsonify({"error": "Failed to update daily review limit"}), 500


@app.route("/get_email", methods=["GET"])
def get_email():
    user_id = request.args.get("user_id", type=int)
    if not user_id:
        logger.warning(f"Email retrieval failed: No user ID provided")
        return jsonify({"error": "User ID is required"}), 400
    email = auth.get_email(user_id)
    if email:
        logger.info(f"Retrieved email for user ID {user_id}")
        return jsonify({"email": email}), 200
    logger.warning(f"Email not found for user ID {user_id}")
    return jsonify({"error": "User not found"}), 404


@app.route("/get_daily_review_limit", methods=["GET"])
def get_daily_review_limit():
    user_id = request.args.get("user_id", type=int)
    if not user_id:
        logger.warning(f"Daily review limit retrieval failed: No user ID provided")
        return jsonify({"error": "User ID is required"}), 400
    daily_review_limit = db_service.user_settings_ops.fetch_daily_review_limit(user_id)
    if daily_review_limit is not None:
        logger.info(
            f"Retrieved daily review limit for user ID {user_id}: {daily_review_limit}"
        )
        return jsonify({"daily_review_limit": daily_review_limit}), 200
    logger.warning(f"Daily review limit not found for user ID {user_id}")
    return jsonify({"error": "User not found"}), 404


if __name__ == "__main__":
    app.run(debug=True)
