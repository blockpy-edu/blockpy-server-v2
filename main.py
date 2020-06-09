import os
from flask import Flask, send_from_directory


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    # load the test config if passed in
    if test_config is not None:
        app.config.from_mapping(test_config)
    elif app.env == 'production':
        app.config.from_object('config.ProductionConfig')
    elif app.env == 'development':
        app.config.from_object('config.DevelopmentConfig')
    app.config.from_pyfile('configuration.py', silent=True)

    app.config['TEMPLATES_AUTO_RELOAD'] = True

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Load up the database
    from models import db
    db.init_app(app)

    # Modify Jinja2
    #from controllers.jinja_filters import setup_jinja_filters

    #setup_jinja_filters(app)

    # Logging
    #from controllers.interaction_logger import setup_logging
    #setup_logging(app)

    # Assets
    #from controllers.assets import assets

    # Email
    #from flask_mail import Mail
    #mail = Mail(app)

    #import controllers

    # a simple page that says hello
    @app.route('/<path:path>', methods=['GET'])
    def static_proxy(path):
        return send_from_directory('./frontend/dist/frontend/', path)

    @app.route('/')
    def root():
        return send_from_directory('./frontend/dist/frontend/', 'index.html')

    return app