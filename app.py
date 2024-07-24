from flask import Flask, request, jsonify
from email_service import send_email
import random
import string

app = Flask(__name__)


@app.route("/send_verification_code", methods=["POST"])
def send_verification_code():
    data = request.json
    email = data.get("email")

    if not email:
        return jsonify({"error": "Email is required"}), 400

    code = "".join(random.choices(string.digits, k=6))

    subject = "Your Verification Code"
    body = f"Your verification code is: {code}"

    if send_email(email, subject, body):
        return jsonify({"status": "Verification code sent"}), 200
    else:
        return jsonify({"error": "Failed to send email"}), 500


if __name__ == "__main__":
    app.run(debug=True)
