import os
import random
import string
import time
import sqlite3
from flask import jsonify
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDER_EMAIL = "physics-revision-app@mail.com"
DATABASE = "otp_db.sqlite3"


# Database connection helper
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# Store OTP in the database
def store_otp(email, otp, expiry):
    conn = get_db_connection()
    c = conn.cursor()

    c.execute(
        """
    INSERT OR REPLACE INTO otp (email, otp, expiry)
    VALUES (?, ?, ?)
    """,
        (email, otp, expiry),
    )

    conn.commit()
    conn.close()


# Retrieve stored OTP from the database
def get_stored_otp(email):
    conn = get_db_connection()
    c = conn.cursor()

    c.execute(
        """
    SELECT otp, expiry FROM otp WHERE email = ?
    """,
        (email,),
    )

    result = c.fetchone()
    conn.close()
    return result


# Clear stored OTP from the database
def clear_stored_otp(email):
    conn = get_db_connection()
    c = conn.cursor()

    c.execute(
        """
    DELETE FROM otp WHERE email = ?
    """,
        (email,),
    )

    conn.commit()
    conn.close()


# Send an email using SendGrid
def send_email(to_email, subject, body):
    message = Mail(
        from_email=SENDER_EMAIL,
        to_emails=to_email,
        subject=subject,
        plain_text_content=body,
    )
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        print(response.status_code)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


# Generate and send OTP to the user's email
def send_verification_code(email):
    otp = "".join(random.choices(string.digits, k=6))
    otp_expiry = time.time() + 60  # OTP valid for 5 minutes

    store_otp(email, otp, otp_expiry)

    subject = "Your Verification Code"
    body = f"Your verification code is: {otp}"

    if send_email(email, subject, body):
        return jsonify({"status": "Verification code sent"}), 200
    else:
        return jsonify({"error": "Failed to send email"}), 500


# Verify the OTP provided by the user
def verify_otp(email, otp):
    stored_otp_data = get_stored_otp(email)

    if not stored_otp_data:
        return jsonify({"error": "OTP not found"}), 400

    stored_otp, expiry = stored_otp_data

    if time.time() > expiry:
        return jsonify({"error": "OTP expired"}), 400

    if otp == stored_otp:
        clear_stored_otp(email)
        return jsonify({"status": "OTP verified"}), 200
    else:
        return jsonify({"error": "Invalid OTP"}), 400
