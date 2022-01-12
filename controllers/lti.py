from controllers.setup import registry, rebar
from flask_rebar import RequestSchema
from marshmallow import fields


#class IdSchema(RequestSchema):
#    id = fields.Integer(required=True)


#@registry.handles(rule='/lti', method='POST', request_body_schema=IdSchema())
#def lti_launch():
#    body = rebar.validated_body
#    given_id = body['id']
#    return f"Hello World @ {given_id}"

