"""
All the controllers in the system get loaded here.
"""
import json

import requests
from flask import current_app, send_from_directory, session, jsonify, Response
from flask_jwt_extended import create_access_token

from controllers.setup import registry, rebar, generator
import controllers.lti
from models.user import User, UserSchema
from controllers.pylti.flask import lti
from hmac import compare_digest

def authenticate(username, password):
    if username=='acbart' and compare_digest("pw".encode('utf-8'), password.encode('utf-8')):
        return True

def identity(payload):
    user_id = payload['identity']
    return {'id': user_id, 'username': 'acbart', 'password': 'pw'}


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


def proxy_localhost_request(path):
    resp = requests.get(f'http://localhost:3000/{path}')
    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    headers = [(name, value) for (name, value) in resp.raw.headers.items() if name.lower() not in excluded_headers]
    return Response(resp.content, resp.status_code, headers)


@current_app.route('/v1/lti', methods=['POST'])
@lti(request='any')
def lti_launch(lti=None):
    """
    :return:
    """
    email = session.get("lis_person_contact_email_primary", "")
    access_token = create_access_token(identity=email)
    response = proxy_localhost_request('')
    response.set_cookie('access_token', access_token, samesite='None', secure=True)
    return response


    #code = f"<script>window.env = {{access_token: {json.dumps(access_token)}}};</script>"
    #frontpage = send_from_directory('./frontend/build/', 'index.html')
    #frontpage.set_cookie('access_token', access_token)
    #frontpage.set_data(code)
    #return frontpage
    #return f"<html><head>{code}</head><body>LTI LAUNCHING for: {email}</body></html>"


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
    return proxy_localhost_request(path)
    #return send_from_directory('./frontend/build/', path)


@current_app.route('/')
def root():
    """
    Serve the main index page.
    """
    return proxy_localhost_request('')
    #return send_from_directory('./frontend/build/', 'index.html')

