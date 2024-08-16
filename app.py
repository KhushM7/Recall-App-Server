from flask import Flask, request, jsonify
from email_service import send_verification_code, verify_otp

app = Flask(__name__)


@app.route("/send_verification_code", methods=["POST"])
def handle_send_verification_code():
    data = request.json
    email = data.get("email")

    if not email:
        return jsonify({"error": "Email is required"}), 400

    return send_verification_code(email)


@app.route("/verify_otp", methods=["POST"])
def handle_verify_otp():
    data = request.json
    email = data.get("email")
    otp = data.get("otp")

    if not email or not otp:
        return jsonify({"error": "Email and OTP are required"}), 400

    return verify_otp(email, otp)


if __name__ == "__main__":
    app.run(debug=True)
