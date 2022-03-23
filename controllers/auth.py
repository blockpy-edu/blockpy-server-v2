from flask import current_app, g, jsonify, make_response, request
from flask_jwt_extended import create_access_token, get_jwt_identity, verify_jwt_in_request, \
    set_access_cookies
from flask_jwt_extended.jwt_manager import ExpiredSignatureError
from flask_jwt_extended.exceptions import NoAuthorizationError
from flask_rebar import RequestSchema
from marshmallow import fields

from controllers.setup import registry, rebar
from models.user import UserSchema


@current_app.before_request
def check_login():
    if request.endpoint in ('lti_launch', 'v1.login'):
        return
    try:
        verify_jwt_in_request()
        g.user = get_jwt_identity()
    except (NoAuthorizationError, ExpiredSignatureError):
        g.user = {"email": "ANONYMOUS", "first_name": "Anonymous@"+request.remote_addr}
    except Exception as e:
        print("WHAT NO", e)
        raise


class LoginSchema(RequestSchema):
    email = fields.String(required=True)
    password = fields.String(required=True)


@registry.handles(rule='/login', method='POST', request_body_schema=LoginSchema, response_body_schema=UserSchema)
def login():
    email = rebar.validated_body['email']
    password = rebar.validated_body['password']

    #user = User.query.filter_by(username=username).one_or_none()
    #if not user or not user.check_password(password):
    #    return jsonify("Wrong username or password"), 401
    user = {"email": email, "first_name": "Unknown:"+email}
    access_token = create_access_token(identity=user)
    response = make_response(jsonify(user))
    set_access_cookies(response, access_token)
    return response
