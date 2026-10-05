from flask import (
    Blueprint, render_template, request, redirect,
    url_for, session, flash
)
from database import db
from models import Event, slugify

admin_bp = Blueprint("admin", __name__)


def _get_my_event():
    email = session.get("owner_email")
    if not email:
        return None
    return Event.query.filter_by(owner_email=email).first()


# ---------- Etkinlik Oluşturucu Girişi ----------
@admin_bp.route("/olusturucu/giris", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        if not email:
            return render_template("admin_login.html", error="E-posta gerekli.")
        session["owner_email"] = email

        event = Event.query.filter_by(owner_email=email).first()
        if event:
            return redirect(url_for("admin.panel"))
        return redirect(url_for("admin.create_event"))

    if session.get("owner_email"):
        return redirect(url_for("admin.panel"))
    return render_template("admin_login.html")


@admin_bp.route("/olusturucu/cikis")
def logout():
    session.pop("owner_email", None)
    return redirect(url_for("home.index"))


# ---------- Etkinlik Oluştur ----------
@admin_bp.route("/etkinlik/olustur", methods=["GET", "POST"])
def create_event():
    if "owner_email" not in session:
        return redirect(url_for("admin.login"))

    if _get_my_event():
        return redirect(url_for("admin.panel"))

    if request.method == "POST":
        name = request.form["name"].strip()
        date = request.form["date"].strip()
        capacity = int(request.form["capacity"])

        base_slug = slugify(name)
        slug = base_slug
        counter = 1
        while Event.query.filter_by(slug=slug).first():
            counter += 1
            slug = f"{base_slug}-{counter}"

        event = Event(
            owner_email=session["owner_email"],
            name=name,
            slug=slug,
            date=date,
            capacity=capacity,
        )
        db.session.add(event)
        db.session.commit()
        flash("Etkinlik oluşturuldu.", "success")
        return redirect(url_for("admin.panel"))

    return render_template("create_event.html", event=None, edit=False)


# ---------- Etkinlik Düzenle ----------
@admin_bp.route("/etkinlik/duzenle", methods=["GET", "POST"])
def edit_event():
    event = _get_my_event()
    if not event:
        return redirect(url_for("admin.create_event"))

    if request.method == "POST":
        event.name = request.form["name"].strip()
        event.date = request.form["date"].strip()
        event.capacity = int(request.form["capacity"])
        db.session.commit()
        flash("Etkinlik güncellendi.", "success")
        return redirect(url_for("admin.panel"))

    return render_template("create_event.html", event=event, edit=True)


# ---------- Panel ----------
@admin_bp.route("/panel")
def panel():
    event = _get_my_event()
    if not event:
        return redirect(url_for("admin.create_event"))

    total_tickets = sum(len(o.tickets) for o in event.orders)
    checked = sum(1 for o in event.orders for t in o.tickets if t.checked_in)
    revenue = sum(o.total or 0 for o in event.orders)

    stats = {
        "orders": len(event.orders),
        "tickets": total_tickets,
        "checked": checked,
        "remaining": event.capacity - total_tickets,
        "revenue": revenue,
    }

    return render_template("panel.html", event=event, stats=stats)