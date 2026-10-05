import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from config import Config, BASE_DIR


def generate_ticket_pdf(ticket, event, order, qr_rel_path: str) -> str:
    os.makedirs(Config.PDF_FOLDER, exist_ok=True)
    file_name = f"bilet_{ticket.ticket_code}.pdf"
    full_path = os.path.join(Config.PDF_FOLDER, file_name)

    c = canvas.Canvas(full_path, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 22)
    c.drawString(30 * mm, height - 30 * mm, "ETKINLIK BILETI")

    c.setFont("Helvetica", 12)
    y = height - 50 * mm
    for line in [
        f"Etkinlik: {event.name}",
        f"Tarih: {event.formatted_date}",
        f"Bilet Turu: {ticket.ticket_type.name}",
        f"Odenen: {ticket.price_paid:.2f} TL",
        f"Bilet ID: {ticket.ticket_code}",
        f"Alici: {order.buyer_name}",
        f"E-posta: {order.buyer_email}",
        f"Telefon: {order.buyer_phone}",
    ]:
        c.drawString(30 * mm, y, line)
        y -= 8 * mm

    qr_full = os.path.join(BASE_DIR, "static", qr_rel_path)
    if os.path.exists(qr_full):
        c.drawImage(ImageReader(qr_full), width - 80 * mm, height - 130 * mm, 60 * mm, 60 * mm)

    c.showPage()
    c.save()
    return f"pdf/{file_name}"