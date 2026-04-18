from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
bcrypt = Bcrypt()
migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)

    from app.main.routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from app.auth.routes import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    from app.wards.routes import wards as wards_blueprint
    app.register_blueprint(wards_blueprint)

    from app.patients.routes import patients as patients_blueprint
    app.register_blueprint(patients_blueprint)

    from app.transfers.routes import transfers as transfers_blueprint
    app.register_blueprint(transfers_blueprint)

    from app.reports.routes import reports as reports_blueprint
    app.register_blueprint(reports_blueprint)

    from app.models import models

    return app
