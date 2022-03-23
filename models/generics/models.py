"""
All the most core components of the models, including the DB and the migrate.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_marshmallow import Marshmallow

# Set up SQLAlchemy
db = SQLAlchemy()

# Set up Marshmallow
ma = Marshmallow()

# Set up Flask-Migrate
migrate = Migrate()
