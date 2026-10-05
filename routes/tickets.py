from flask import (
    Blueprint, render_template, request, redirect,
    url_for, session, flash
)
from database import db
from models import Event, TicketType, DiscountCode

tickets_bp = Blueprint("tickets", __name__)


def _get_event():
    return Event.query.filter_by(owner_email=session.get("owner_email")).first()


# ---------------- BİLET AYARLARI ----------------
@tickets_bp.route("/bilet-ayarlari", methods=["GET", "POST"])
def settings():
    event = _get_event()
    if not event:
        return redirect(url_for("admin.create_event"))

    if request.method == "POST":
        action = request.form.get("action")

        if action == "add_type":
            db.session.add(TicketType(
                event_id=event.id,
                name=request.form["name"].strip(),
                price=float(request.form["price"]),
            ))
        elif action == "add_discount":
            db.session.add(DiscountCode(
                event_id=event.id,
                code=request.form["code"].strip().upper(),
                percent=int(request.form["percent"]),
            ))
        db.session.commit()
        flash("Kaydedildi.", "success")
        return redirect(url_for("tickets.settings"))

    return render_template(
        "ticket_settings.html",
        event=event,
        ticket_types=event.ticket_types,
        discounts=DiscountCode.query.filter_by(event_id=event.id).all(),
    )


@tickets_bp.route("/bilet-turu/<int:tt_id>/sil", methods=["POST"])
def delete_type(tt_id):
    event = _get_event()
    tt = TicketType.query.filter_by(id=tt_id, event_id=event.id).first_or_404()
    db.session.delete(tt)
    db.session.commit()
    return redirect(url_for("tickets.settings"))


@tickets_bp.route("/bilet-turu/<int:tt_id>/duzenle", methods=["POST"])
def edit_type(tt_id):
    event = _get_event()
    tt = TicketType.query.filter_by(id=tt_id, event_id=event.id).first_or_404()
    tt.name = request.form["name"].strip()
    tt.price = float(request.form["price"])
    db.session.commit()
    return redirect(url_for("tickets.settings"))


@tickets_bp.route("/indirim/<int:dc_id>/sil", methods=["POST"])
def delete_discount(dc_id):
    event = _get_event()
    dc = DiscountCode.query.filter_by(id=dc_id, event_id=event.id).first_or_404()
    db.session.delete(dc)
    db.session.commit()
    return redirect(url_for("tickets.settings"))


# ---------------- KATILIMCILAR ----------------
@tickets_bp.route("/katilimcilar")
def participants():
    event = _get_event()
    if not event:
        return redirect(url_for("admin.create_event"))

    orders = event.orders

    # ---- Özet hesaplamaları (Python tarafında) ----
    # Her sipariş birden fazla bilet içerebilir; bu yüzden tickets listelerini
    # tek tek dolaşıp toplam çıkarıyoruz.
    total_orders = len(orders)
    total_tickets = 0
    total_checked = 0
    total_revenue = 0.0

    for o in orders:
        total_tickets += len(o.tickets)
        total_revenue += (o.total or 0.0)
        for t in o.tickets:
            if t.checked_in:
                total_checked += 1

    summary = {
        "orders": total_orders,
        "tickets": total_tickets,
        "checked": total_checked,
        "revenue": total_revenue,
    }

    return render_template(
        "participants.html",
        event=event,
        orders=orders,
        summary=summary,
    )