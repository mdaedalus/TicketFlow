"""
E-posta gönderme modülü. Şu anda sistem tarafından ÇAĞRILMIYOR.
Kullanmak için config.py'da MAIL_ENABLED = True yap ve bilgileri doldur.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import Config


def send_ticket_email(to_email: str, subject: str, body: str) -> bool:
    if not Config.MAIL_ENABLED:
        print(f"[MAIL-PASIF] Gönderilecek: {to_email} | {subject}")
        return False

    try:
        msg = MIMEMultipart()
        msg["From"] = Config.MAIL_SENDER
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))

        with smtplib.SMTP(Config.MAIL_SERVER, Config.MAIL_PORT) as server:
            server.starttls()
            server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print("[MAIL-HATA]", e)
        return False