import smtplib
from email.mime.text import MIMEText
from config import EMAIL_USER, EMAIL_PASSWORD, SMTP_SERVER, SMTP_PORT


def send_email(to_email, subject, body):
    try:
        msg = MIMEText(body, "plain")
        msg["From"] = EMAIL_USER
        msg["To"] = to_email
        msg["Subject"] = subject

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.send_message(msg)

        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False
