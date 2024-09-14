import os
import random
import sqlite3
import ssl
import string
import time
from typing import Optional, Tuple

import urllib3
from flask import jsonify, Response
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Content, From, To

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
DATABASE = "Reset_Password/otp_db.sqlite3"

ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def load_email_template(
    file_path: str,
    otp: str,
) -> str:
    with open(file_path, "r") as file:
        template = file.read()
    return template.replace("otp", otp)


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
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


def send_email(to_email: str, subject: str, html_content: str) -> bool:
    message = Mail(
        from_email=From(SENDER_EMAIL, "Physics Revision App"),
        to_emails=To(to_email),
        subject=subject,
        html_content=Content("text/html", html_content),
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

    subject = f"Your Verification Code is {otp}"
    html_content = load_email_template("Reset_Password/email_template.html", otp)

    if send_email(email, subject, html_content):
        return jsonify({"status": "Verification code sent"}), 200
    else:
        return jsonify({"error": "Failed to send email"}), 500


def verify_otp(email: str, otp: str) -> Tuple[Response, int]:
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
