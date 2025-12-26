import os
import smtplib
from email.message import EmailMessage

def send_email(to, subject, message):
    msg = EmailMessage()
    msg["From"] = os.getenv("SENDER_EMAIL")
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(message)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(
            os.getenv("SENDER_EMAIL"),
            os.getenv("SENDER_PASSWORD")
        )
        smtp.send_message(msg)
