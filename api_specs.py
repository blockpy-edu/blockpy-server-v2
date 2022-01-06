from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from apispec_webframeworks.flask import FlaskPlugin


spec = APISpec(
    title="BlockPy Server API",
    version="1.0.0",
    openapi_version="3.0.2",
    info=dict(
        description="BlockPy Server API",
        version="1.0.0-oas3",
        contact=dict(
            email="acbart9@gmail.com"
            ),
        license=dict(
            name="Apache 2.0",
            url='https://www.apache.org/licenses/LICENSE-2.0.html'
            )
        ),
    plugins=[MarshmallowPlugin()],
)
