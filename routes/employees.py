from flask import (
    Blueprint, render_template, request, redirect,
    url_for, session, flash
)
from database import db
from models import Event, Employee

employees_bp = Blueprint("employees", __name__)


def _get_event():
    return Event.query.filter_by(owner_email=session.get("owner_email")).first()


@employees_bp.route("/calisanlar", methods=["GET", "POST"])
def list_employees():
    event = _get_event()
    if not event:
        return redirect(url_for("admin.create_event"))

    if request.method == "POST":
        emp = Employee(
            event_id=event.id,
            first_name=request.form["first_name"].strip(),
            last_name=request.form["last_name"].strip(),
            phone=request.form["phone"].strip(),
            password=request.form["password"].strip(),
        )
        db.session.add(emp)
        db.session.commit()
        flash("Çalışan eklendi.", "success")
        return redirect(url_for("employees.list_employees"))

    return render_template("employees.html", event=event, employees=event.employees)


@employees_bp.route("/calisanlar/<int:emp_id>/sil", methods=["POST"])
def delete_employee(emp_id):
    event = _get_event()
    emp = Employee.query.filter_by(id=emp_id, event_id=event.id).first_or_404()
    db.session.delete(emp)
    db.session.commit()
    flash("Çalışan silindi.", "success")
    return redirect(url_for("employees.list_employees"))


@employees_bp.route("/calisanlar/<int:emp_id>/duzenle", methods=["POST"])
def edit_employee(emp_id):
    event = _get_event()
    emp = Employee.query.filter_by(id=emp_id, event_id=event.id).first_or_404()
    emp.first_name = request.form["first_name"].strip()
    emp.last_name = request.form["last_name"].strip()
    emp.phone = request.form["phone"].strip()
    if request.form.get("password", "").strip():
        emp.password = request.form["password"].strip()
    db.session.commit()
    flash("Çalışan güncellendi.", "success")
    return redirect(url_for("employees.list_employees"))