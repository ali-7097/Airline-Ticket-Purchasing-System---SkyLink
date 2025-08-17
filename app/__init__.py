from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import Config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    from app import models
    from app.models import User
    from app.routes import auth, passenger, admin
    from flask import render_template

    app.register_blueprint(auth.bp)
    app.register_blueprint(passenger.bp)
    app.register_blueprint(admin.bp)


    @app.errorhandler(403)
    def forbidden(e):
        return render_template('403.html'), 403

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    login_manager.login_view = "auth.login"

    return app

