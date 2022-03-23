"""
All the controllers in the system get loaded here.
"""

from flask import current_app, g, redirect
from controllers.setup import registry, rebar, generator
import controllers.lti
from controllers.pylti.flask import lti
import controllers.auth


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


@current_app.route('/')
def root():
    """
    Serve the main index page.
    """
    return redirect(current_app.config['PROXY_SERVER'])
