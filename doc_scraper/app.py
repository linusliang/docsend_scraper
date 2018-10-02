from flask import Flask

import doc_scraper.views as views
from doc_scraper.extensions import socketio, bootstrap
from doc_scraper.logger import setup_logging
from doc_scraper.settings import DEBUG


def create_app(config_object='doc_scraper.settings'):
    setup_logging(DEBUG)
    app = Flask(__name__.split('.')[0])
    app.config.from_object(config_object)
    register_extensions(app)
    register_blueprints(app)
    return app


def register_extensions(app):
    socketio.init_app(app)
    bootstrap.init_app(app)


def register_blueprints(app):
    app.register_blueprint(views.main.blueprint)
