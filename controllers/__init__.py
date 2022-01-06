"""
All the controllers in the system get loaded here.
"""
from flask import current_app, send_from_directory
from controllers.setup import registry, rebar, generator

from models.user import User, UserSchema


@registry.handles(rule='/user', method='GET', response_body_schema=UserSchema(many=True))
def get_users():
    return []


def create_blueprints(app):
    """
    Register all the routes of our project here.
    :param app: The main application context
    :return:
    """
    rebar.init_app(app)


@current_app.route('/debug', methods=['GET'])
def debug_page():
    """
    :return:
    """
    return "<html><body>Debug Page</body></html>"


@current_app.route('/<path:path>', methods=['GET'])
def static_proxy(path):
    """
    Forward all HTML requests to the frontend directory
    :param path:
    :return:
    """
    return send_from_directory('./frontend/build/', path)


@current_app.route('/')
def root():
    """
    Serve the main index page.
    """
    return send_from_directory('./frontend/build/', 'index.html')

