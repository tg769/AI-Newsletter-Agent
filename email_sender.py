import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()


def send_briefing(subject: str, html_body: str) -> None:
    """
    Send the morning briefing email via Gmail SMTP.
    Requires GMAIL_ADDRESS, GMAIL_APP_PASSWORD, and RECIPIENT_EMAIL in .env
    """
    gmail_address = os.environ["GMAIL_ADDRESS"].strip()
    app_password = os.environ["GMAIL_APP_PASSWORD"].strip()
    recipient = os.environ["RECIPIENT_EMAIL"].strip()

    recipients = [recipient, "pratikmishra.edu@gmail.com"]

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"Morning Briefing <{gmail_address}>"
    msg["To"] = ", ".join(recipients)

    msg.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.ehlo()
        server.starttls()
        server.login(gmail_address, app_password)
        server.sendmail(gmail_address, recipients, msg.as_string())

    print(f"[email_sender] Email sent to {', '.join(recipients)}")
