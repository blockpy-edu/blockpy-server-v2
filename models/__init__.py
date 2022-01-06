"""
The models and database connections
"""
from flask import Flask
from models.models import db, migrate, ma
from models.assignment_tag_membership import assignment_tag_membership
from models.user import User
from models.course import Course
from models.assignment import Assignment
from models.assignment_tag import AssignmentTag
from models.assignment_group import AssignmentGroup
from models.assignment_group_membership import AssignmentGroupMembership
from models.authentication import Authentication
from models.log import Log
from models.role import Role
from models.review import Review
from models.submission import Submission
from models.sample_submission import SampleSubmission


def init_database(app: Flask) -> Flask:
    """
    Initialize the database.

    :param app: The main Flask application
    :return: The same (modified) Flask application
    """
    db.init_app(app)
    migrate.init_app(app, db)
    ma.init_app(app)

    return app


#: A listing of all the tables
ALL_TABLES = (Assignment, AssignmentTag, AssignmentGroup, AssignmentGroupMembership,
              Authentication, Course, Log, Role, Review, Submission, User, SampleSubmission)
