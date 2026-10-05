import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "degistir-bunu-uretimde")
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "instance", "etkinlik.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    QR_FOLDER = os.path.join(BASE_DIR, "static", "qr")
    PDF_FOLDER = os.path.join(BASE_DIR, "static", "pdf")

    # E-posta ayarları (opsiyonel - şu an pasif)
    MAIL_ENABLED = False
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USERNAME = ""
    MAIL_PASSWORD = ""
    MAIL_SENDER = ""