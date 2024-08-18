from typing import Tuple

from flask import Flask
from flask import request, jsonify, Response

from email_service import send_verification_code, verify_otp

app = Flask(__name__)


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


if __name__ == "__main__":
    app.run(debug=True)
