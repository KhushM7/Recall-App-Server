import os
import random
import sqlite3
import string
import time
from typing import Optional
from typing import Tuple

from flask import jsonify, Response
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
DATABASE = "otp_db.sqlite3"


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = (
        sqlite3.Row
    )  # Row can now be accessed by both column name and index
    return conn


def store_otp(email: str, otp: str, expiry: float):
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


def get_stored_otp(email: str) -> Optional[sqlite3.Row]:
    """Retrieves the stored OTP and Expiry for the given email address"""
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


def clear_stored_otp(email: str):
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


def send_email(to_email: str, subject: str, body: str) -> bool:
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


def send_verification_code(email: str) -> Tuple[Response, int]:
    otp = "".join(random.choices(string.digits, k=6))
    otp_expiry = time.time() + 60  # OTP valid for 1 minute

    store_otp(email, otp, otp_expiry)

    subject = "Your Verification Code"
    body = f"Your verification code is: {otp}"

    # `jsonify` is a Flask function that converts a dictionary into a JSON response to send back to the client
    if send_email(email, subject, body):
        return jsonify({"status": "Verification code sent"}), 200
    else:
        return jsonify({"error": "Failed to send email"}), 500


def verify_otp(email: str, otp: str) -> Tuple[Response, int]:
    stored_otp, expiry = get_stored_otp(email)

    if not stored_otp or not expiry:
        return jsonify({"error": "OTP not found"}), 400

    if time.time() > expiry:
        return jsonify({"error": "OTP expired"}), 400

    if otp == stored_otp:
        clear_stored_otp(email)
        return jsonify({"status": "OTP verified"}), 200
    else:
        return jsonify({"error": "Invalid OTP"}), 400
