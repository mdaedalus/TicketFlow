import re
import uuid
from datetime import datetime
from database import db


def slugify(text: str) -> str:
    tr = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
    text = text.translate(tr).lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text or uuid.uuid4().hex[:8]


def generate_ticket_code():
    return uuid.uuid4().hex[:12].upper()


class Event(db.Model):
    __tablename__ = "events"
    id = db.Column(db.Integer, primary_key=True)
    owner_email = db.Column(db.String(255), nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(300), unique=True, nullable=False, index=True)
    date = db.Column(db.String(64), nullable=False)          # "2025-06-15T20:00"
    capacity = db.Column(db.Integer, nullable=False)
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    ticket_types = db.relationship("TicketType", backref="event", cascade="all, delete-orphan")
    employees = db.relationship("Employee", backref="event", cascade="all, delete-orphan")
    orders = db.relationship("Order", backref="event", cascade="all, delete-orphan")

    @property
    def formatted_date(self):
        """2025-06-15T20:00 → 15.06.2025 20:00"""
        try:
            dt = datetime.strptime(self.date, "%Y-%m-%dT%H:%M")
            return dt.strftime("%d.%m.%Y %H:%M")
        except Exception:
            return self.date


class Employee(db.Model):
    __tablename__ = "employees"
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(30), nullable=False)
    password = db.Column(db.String(100), nullable=False)


class TicketType(db.Model):
    __tablename__ = "ticket_types"
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False, default=0.0)


class DiscountCode(db.Model):
    __tablename__ = "discount_codes"
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)
    code = db.Column(db.String(50), nullable=False)
    percent = db.Column(db.Integer, nullable=False)


class Order(db.Model):
    __tablename__ = "orders"
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)
    buyer_name = db.Column(db.String(200), nullable=False)
    buyer_email = db.Column(db.String(255), nullable=False)
    buyer_phone = db.Column(db.String(30), nullable=False)
    discount_code = db.Column(db.String(50))
    subtotal = db.Column(db.Float, default=0.0)
    total = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    tickets = db.relationship("Ticket", backref="order", cascade="all, delete-orphan")


class Ticket(db.Model):
    __tablename__ = "tickets"
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    ticket_type_id = db.Column(db.Integer, db.ForeignKey("ticket_types.id"), nullable=False)
    ticket_code = db.Column(db.String(32), unique=True, default=generate_ticket_code)
    price_paid = db.Column(db.Float, nullable=False, default=0.0)
    checked_in = db.Column(db.Boolean, default=False)
    checked_in_at = db.Column(db.DateTime)

    ticket_type = db.relationship("TicketType")