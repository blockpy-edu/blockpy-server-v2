from flask.views import MethodView
from flask_rebar import errors, Rebar, SwaggerV3Generator
from flask_apispec import marshal_with, MethodResource, FlaskApiSpec, doc

rebar = Rebar()
generator = SwaggerV3Generator()
registry = rebar.create_handler_registry(prefix='/v1', swagger_generator=generator)
