from flask import g
from controllers.setup import registry
from models.user import UserSchema


@registry.handles(rule='/me', method='GET', response_body_schema=UserSchema)
def me():
    return g.user
