from controllers.setup import registry, rebar
from flask_rebar import RequestSchema
from marshmallow import fields
from flask import current_app, g, session, jsonify, make_response, redirect, request
from flask_jwt_extended import create_access_token, get_jwt_identity, verify_jwt_in_request, \
    set_access_cookies
from flask_jwt_extended.jwt_manager import ExpiredSignatureError
from flask_jwt_extended.exceptions import NoAuthorizationError
from flask_rebar import RequestSchema
from marshmallow import fields

from controllers.setup import registry, rebar, generator
import controllers.lti
from models.course import CourseSchema
from models.user import UserSchema
from controllers.pylti.flask import lti


@current_app.route('/v1/lti', methods=['POST'])
@lti(request='initial')
def lti_launch(lti=None):
    """
    :return:
    """
    email = session.get("lis_person_contact_email_primary", "")
    full_name = session.get("lis_person_name_full", "")
    access_token = create_access_token(identity={"email": email, "first_name": full_name})
    response = make_response(redirect(current_app.config['PROXY_SERVER']))
    set_access_cookies(response, access_token)
    print(response)
    return response
