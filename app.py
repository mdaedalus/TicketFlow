import os
from flask import Flask
from config import Config
from database import db
from routes.home import home_bp
from routes.admin import admin_bp
from routes.employees import employees_bp
from routes.tickets import tickets_bp
from routes.purchase import purchase_bp
from routes.checkin import checkin_bp


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(Config.QR_FOLDER, exist_ok=True)
    os.makedirs(Config.PDF_FOLDER, exist_ok=True)

    db.init_app(app)

    app.register_blueprint(home_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(employees_bp)
    app.register_blueprint(tickets_bp)
    app.register_blueprint(purchase_bp)
    app.register_blueprint(checkin_bp)

    @app.template_filter("tl")
    def tl_filter(value):
        try:
            return f"{float(value):.2f} TL"
        except Exception:
            return value

    with app.app_context():
        db.create_all()

    return app


if __name__ == "__main__":
    create_app().run(debug=True)