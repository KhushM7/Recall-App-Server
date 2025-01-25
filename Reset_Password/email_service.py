import os
import random
import sqlite3
import ssl
import string
import time
import logging
from typing import Optional, Tuple

import urllib3
from flask import jsonify, Response
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Content, From, To

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
DATABASE = "./physics_revision_app.db"

# Configure the centralized logger
logging.basicConfig(
    filename="application.log",
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def load_email_template(
    file_path: str,
    otp: str,
) -> str:
    with open(file_path, "r") as file:
        template = file.read()
    logger.info("Loaded email template from %s", file_path)
    return template.replace("otp", otp)


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    logger.info("Database connection established")
    return conn


def store_otp(email: str, otp: str, expiry: float):
    conn = get_db_connection()
    c = conn.cursor()

    try:
        c.execute(
            """
        INSERT OR REPLACE INTO otp (email, otp, expiry)
        VALUES (?, ?, ?)
        """,
            (email, otp, expiry),
        )
        conn.commit()
        logger.info("Stored OTP for email: %s", email)
    except sqlite3.Error as e:
        logger.error("Failed to store OTP for email %s: %s", email, e)
    finally:
        conn.close()


def get_stored_otp(email: str) -> Optional[sqlite3.Row]:
    conn = get_db_connection()
    c = conn.cursor()

    try:
        c.execute(
            """
        SELECT otp, expiry FROM otp WHERE email = ?
        """,
            (email,),
        )
        result = c.fetchone()
        logger.info("Retrieved stored OTP for email: %s", email)
        return result
    except sqlite3.Error as e:
        logger.error("Failed to retrieve OTP for email %s: %s", email, e)
        return None
    finally:
        conn.close()


def clear_stored_otp(email: str):
    conn = get_db_connection()
    c = conn.cursor()

    try:
        c.execute(
            """
        DELETE FROM otp WHERE email = ?
        """,
            (email,),
        )
        conn.commit()
        logger.info("Cleared OTP for email: %s", email)
    except sqlite3.Error as e:
        logger.error("Failed to clear OTP for email %s: %s", email, e)
    finally:
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
        logger.info(
            "Email sent to %s with status code %d", to_email, response.status_code
        )
        return True
    except Exception as e:
        logger.error("Error sending email to %s: %s", to_email, e)
        return False


def send_verification_code(email: str) -> Tuple[Response, int]:
    otp = "".join(random.choices(string.digits, k=6))
    otp_expiry = time.time() + 60  # OTP valid for 1 minute

    store_otp(email, otp, otp_expiry)

    subject = f"Your Verification Code is {otp}"
    html_content = load_email_template("Reset_Password/email_template.html", otp)

    if send_email(email, subject, html_content):
        logger.info("Verification code sent to %s", email)
        return jsonify({"status": "Verification code sent"}), 200
    else:
        logger.error("Failed to send verification code to %s", email)
        return jsonify({"error": "Failed to send email"}), 500


def verify_otp(email: str, otp: str) -> Tuple[Response, int]:
    stored_otp_data = get_stored_otp(email)

    if not stored_otp_data:
        logger.warning("OTP not found for email: %s", email)
        return jsonify({"error": "OTP not found"}), 400

    stored_otp, expiry = stored_otp_data

    if time.time() > expiry:
        logger.warning("OTP expired for email: %s", email)
        return jsonify({"error": "OTP expired"}), 400

    if otp == stored_otp:
        clear_stored_otp(email)
        logger.info("OTP verified for email: %s", email)
        return jsonify({"status": "OTP verified"}), 200
    else:
        logger.warning("Invalid OTP for email: %s", email)
        return jsonify({"error": "Invalid OTP"}), 400
