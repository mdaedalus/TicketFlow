import os
import qrcode
from config import Config


def generate_qr(ticket_code: str) -> str:
    os.makedirs(Config.QR_FOLDER, exist_ok=True)
    file_name = f"{ticket_code}.png"
    img = qrcode.make(ticket_code)
    img.save(os.path.join(Config.QR_FOLDER, file_name))
    return f"qr/{file_name}"