from datetime import datetime
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, session
)
from database import db
from models import Employee, Ticket

checkin_bp = Blueprint("checkin", __name__)


@checkin_bp.route("/calisan/giris", methods=["GET", "POST"])
def employee_login():
    if request.method == "POST":
        phone = request.form["phone"].strip()
        password = request.form["password"].strip()

        emp = Employee.query.filter_by(phone=phone, password=password).first()
        if not emp:
            return render_template("checkin_login.html", error="Geçersiz giriş.")
        session["employee_id"] = emp.id
        return redirect(url_for("checkin.scan"))

    return render_template("checkin_login.html")


@checkin_bp.route("/calisan/cikis")
def employee_logout():
    session.pop("employee_id", None)
    return redirect(url_for("home.index"))


@checkin_bp.route("/calisan/tara", methods=["GET", "POST"])
def scan():
    emp_id = session.get("employee_id")
    if not emp_id:
        return redirect(url_for("checkin.employee_login"))

    emp = Employee.query.get(emp_id)
    event = emp.event
    result = None

    if request.method == "POST":
        code = request.form["ticket_code"].strip().upper()
        ticket = Ticket.query.filter_by(ticket_code=code).first()

        if not ticket or ticket.order.event_id != event.id:
            result = {"ok": False, "msg": "Geçersiz bilet."}
        elif ticket.checked_in:
            result = {"ok": False, "msg": f"Bu bilet zaten kullanılmış ({ticket.checked_in_at.strftime('%d.%m %H:%M')})."}
        else:
            ticket.checked_in = True
            ticket.checked_in_at = datetime.utcnow()
            db.session.commit()
            result = {"ok": True, "msg": f"✅ Giriş onaylandı: {ticket.order.buyer_name} ({ticket.ticket_type.name})"}

    return render_template("checkin.html", employee=emp, event=event, result=result)