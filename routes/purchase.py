import os
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, session, send_file, flash
)
from database import db
from models import Event, TicketType, DiscountCode, Order, Ticket
from utils.qr_generator import generate_qr
from utils.pdf_generator import generate_ticket_pdf
from utils.mailer import send_ticket_email
from config import Config

purchase_bp = Blueprint("purchase", __name__)


# ---------- Ödeme fonksiyonu (ŞU AN PASİF) ----------
def process_payment(order_data: dict) -> bool:
    """
    ⚠️ Şu anda pasif. Her zaman True döner.
    İleride iyzico / stripe / paytr entegrasyonu buraya gelecek.
    """
    print(f"[ODEME-PASIF] Sipariş #{order_data.get('order_id')} | "
          f"Tutar: {order_data.get('total')} TL — Ödeme alınmadı (demo).")
    return True


# ---------- 1. Herkese açık etkinlik listesi ----------
@purchase_bp.route("/bilet-al")
def public_events():
    events = Event.query.filter_by(is_published=True) \
                        .order_by(Event.created_at.desc()).all()
    return render_template("public_events.html", events=events)


# ---------- 2. Etkinlik detayı (bilet türleri) ----------
@purchase_bp.route("/bilet-al/<slug>")
def public_event_detail(slug):
    event = Event.query.filter_by(slug=slug, is_published=True).first_or_404()
    return render_template("public_event_detail.html", event=event)


# ---------- 3. Sepeti al → checkout sayfası ----------
@purchase_bp.route("/bilet-al/<slug>/onayla", methods=["POST"])
def public_cart(slug):
    event = Event.query.filter_by(slug=slug, is_published=True).first_or_404()

    selections = {}
    for key, value in request.form.items():
        if key.startswith("qty_"):
            try:
                tt_id = int(key.split("_")[1])
                qty = int(value)
                if qty > 0:
                    selections[tt_id] = qty
            except ValueError:
                continue

    if not selections:
        flash("En az bir bilet seçmelisiniz.", "error")
        return redirect(url_for("purchase.public_event_detail", slug=slug))

    session["cart"] = {
        "event_id": event.id,
        "selections": selections,
        "discount_code": request.form.get("discount_code", "").strip().upper(),
    }
    return redirect(url_for("purchase.public_checkout", slug=slug))


# ---------- 4. Checkout (bilgiler + satın al) ----------
@purchase_bp.route("/bilet-al/<slug>/odeme", methods=["GET", "POST"])
def public_checkout(slug):
    event = Event.query.filter_by(slug=slug, is_published=True).first_or_404()
    cart = session.get("cart")
    if not cart or cart.get("event_id") != event.id:
        return redirect(url_for("purchase.public_event_detail", slug=slug))

    # Sepet satırları
    items, subtotal = [], 0.0
    for tt_id, qty in cart["selections"].items():
        tt = TicketType.query.get(tt_id)
        if not tt:
            continue
        line_total = tt.price * qty
        subtotal += line_total
        items.append({"tt": tt, "qty": qty, "line_total": line_total})

    # İndirim kontrolü
    discount = None
    if cart.get("discount_code"):
        discount = DiscountCode.query.filter_by(
            event_id=event.id, code=cart["discount_code"]).first()

    discount_amount = subtotal * (discount.percent / 100.0) if discount else 0.0
    total = subtotal - discount_amount

    # ---- Satın al ----
    if request.method == "POST":
        buyer_name = request.form["buyer_name"].strip()
        buyer_email = request.form["buyer_email"].strip().lower()
        buyer_phone = request.form["buyer_phone"].strip()

        order = Order(
            event_id=event.id,
            buyer_name=buyer_name,
            buyer_email=buyer_email,
            buyer_phone=buyer_phone,
            discount_code=discount.code if discount else None,
            subtotal=subtotal,
            total=total,
        )
        db.session.add(order)
        db.session.flush()  # id al

        # ⚠️ Ödeme pasif ama fonksiyon çağrılıyor (ileride doldurulacak)
        if not process_payment({"order_id": order.id, "total": total}):
            db.session.rollback()
            flash("Ödeme başarısız.", "error")
            return redirect(url_for("purchase.public_checkout", slug=slug))

        created = []
        for item in items:
            unit_price = item["tt"].price
            if discount:
                unit_price *= (1 - discount.percent / 100.0)
            for _ in range(item["qty"]):
                t = Ticket(
                    order_id=order.id,
                    ticket_type_id=item["tt"].id,
                    price_paid=round(unit_price, 2),
                )
                db.session.add(t)
                created.append(t)
        db.session.commit()

        # QR + PDF üret
        for t in created:
            qr_rel = generate_qr(t.ticket_code)
            generate_ticket_pdf(t, event, order, qr_rel)

        # E-posta (pasif, çağrılıyor ama göndermiyor)
        send_ticket_email(
            buyer_email,
            f"Biletleriniz: {event.name}",
            "Bilet ID'leriniz: " + ", ".join(t.ticket_code for t in created),
        )

        session.pop("cart", None)
        return redirect(url_for("purchase.order_success", order_id=order.id))

    return render_template(
        "public_checkout.html",
        event=event, items=items, subtotal=subtotal,
        discount=discount, discount_amount=discount_amount, total=total,
    )


# ---------- 5. Başarılı sipariş ----------
@purchase_bp.route("/siparis/<int:order_id>/basarili")
def order_success(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template("order_success.html", order=order, event=order.event)


# ---------- 6. PDF indir ----------
@purchase_bp.route("/bilet/<ticket_code>/pdf")
def download_pdf(ticket_code):
    ticket = Ticket.query.filter_by(ticket_code=ticket_code).first_or_404()
    file_name = f"bilet_{ticket.ticket_code}.pdf"
    full_path = os.path.join(Config.PDF_FOLDER, file_name)
    if not os.path.exists(full_path):
        qr_rel = generate_qr(ticket.ticket_code)
        generate_ticket_pdf(ticket, ticket.order.event, ticket.order, qr_rel)
    return send_file(full_path, as_attachment=True, download_name=file_name)


# ---------- 7. Bilet sorgulama ----------
# ---------- 7. Bilet sorgulama (3 seçenekli) ----------
@purchase_bp.route("/bilet-sorgula", methods=["GET", "POST"])
def query_ticket():
    results = None
    error = None
    query_type = None
    query_value = None

    if request.method == "POST":
        query_type = request.form.get("query_type", "").strip()
        query_value = request.form.get("query_value", "").strip()

        if not query_value:
            error = "Lütfen bir değer girin."
        else:
            orders = []
            if query_type == "phone":
                orders = Order.query.filter(
                    Order.buyer_phone.ilike(f"%{query_value}%")
                ).order_by(Order.created_at.desc()).all()

            elif query_type == "email":
                orders = Order.query.filter(
                    Order.buyer_email.ilike(f"%{query_value}%")
                ).order_by(Order.created_at.desc()).all()

            elif query_type == "ticket_id":
                # Bilet ID'si ile ara → ticket bul → order'ı al
                t = Ticket.query.filter(
                    Ticket.ticket_code.ilike(f"%{query_value.upper()}%")
                ).first()
                if t:
                    orders = [t.order]

            else:
                error = "Geçersiz sorgu türü."

            if not error and not orders:
                error = "Kayıt bulunamadı."

            if orders:
                results = orders

    return render_template(
        "ticket_query.html",
        results=results,
        error=error,
        query_type=query_type,
        query_value=query_value,
    )