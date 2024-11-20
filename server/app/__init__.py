from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    # initialize the database
    db.init_app(app)

    from app.routes.main_routes import main
    from app.routes.api_routes import api

    app.register_blueprint(main)
    app.register_blueprint(api, url_prefix="/api")

    return app
