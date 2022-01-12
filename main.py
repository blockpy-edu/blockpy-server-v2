import os
from flask import Flask
from flask_debugtoolbar import DebugToolbarExtension
from flask_jwt_extended import JWTManager

from api_specs import spec


def create_app(test_config=None) -> Flask:
    """
    Per the App Factory pattern, this creates a new instance of the BlockPy app.
    :param test_config: 'testing' for unit tests, or a specific config object.
    :return:
    """
    # create and configure the app
    app = Flask('blockpy', instance_relative_config=True, static_folder=None)
    # load the test config if passed in
    if test_config is not None:
        if test_config == 'testing':
            app.config.from_object('config.TestConfig')
        else:
            app.config.from_mapping(test_config)
    elif app.env == 'production':
        app.config.from_object('config.ProductionConfig')
    elif app.env == 'development':
        app.config.from_object('config.DevelopmentConfig')
    app.config.from_pyfile('configuration.py')

    # Additional settings being overridden here
    app.config['TEMPLATES_AUTO_RELOAD'] = True

    # Set up the API Spec information
    # TODO: Consider moving this to a static file
    app.config.update({'APISPEC_SPEC': spec})

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Load up the database
    from models import init_database
    init_database(app)

    # Turn on Debug Toolbar
    DebugToolbarExtension(app)

    # Set Up JWT
    jwt = JWTManager(app)

    # Modify Jinja2
    # from controllers.jinja_filters import setup_jinja_filters

    # setup_jinja_filters(app)

    # Logging
    # from controllers.interaction_logger import setup_logging
    # setup_logging(app)

    # Assets
    # from controllers.assets import assets

    # Email
    # from flask_mail import Mail
    # mail = Mail(app)

    # Set up all the endpoints
    with app.app_context():
        from controllers import create_blueprints
        create_blueprints(app)

    return app
