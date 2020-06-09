import logging
from collections import OrderedDict
import json

from sqlalchemy import Column, String, Integer, ForeignKey, Text, func, JSON

from models.assignment import Assignment
import models
from models.models import db
from models.base import Base
from common.dates import datetime_to_string, string_to_datetime
from models.user import User


class Log(Base):
    # Identification
    assignment_id = Column(Integer(), ForeignKey('assignment.id'))
    assignment_version = Column(Integer())
    course_id = Column(Integer(), ForeignKey('course.id'))
    subject_id = Column(Integer(), ForeignKey('user.id'))
    # Actual event data
    event_type = Column(String(255))
    file_path = Column(String(255), default="", nullable=True)
    category = Column(String(255), default="")
    label = Column(String(255), default="")
    # Message will be JSON encoded data
    message = Column(Text(), default="")
    client_timestamp = Column(String(255), default="")
    client_timezone = Column(String(255), default="")

    assignment = db.relationship("Assignment")
    subject = db.relationship("User")
    course = db.relationship("Course")

    # event_type
    # => event_id
    # subject_id
    # => tool_instances
    # => code_state_id
    # => server_timestamp
    # => server_timezone
    # client_timestamp
    # => client_timezone
    # => session_id
    # course_id
    # => term_id
    # assignment_id
    # => edit_type
    # file_path
    # ? body
    # => execution_result
    # => SyntaxError: compile_result, compile_message_type, compile_message_data
    # => Feedback: intervention_type, intervention_message
    # => RunTime Error: program_input, program_output, program_error_output
    # => source_location (line of code with error)
    # => score

    def encode_json(self):
        return {
            '_schema_version': 2,
            'id': self.id,
            'date_modified': datetime_to_string(self.date_modified),
            'date_created': datetime_to_string(self.date_created),

            'assignment_id': self.assignment_id,
            'assignment_version': self.assignment_version,
            'course_id': self.course_id,
            'subject_id': self.subject_id,
            'event_type': self.event_type,
            'file_path': self.file_path,
            'category': self.category,
            'label': self.label,
            'message': self.message,
            'client_timestamp': self.client_timestamp,
            'client_timezone': self.client_timezone
        }

    @staticmethod
    def new(assignment_id, assignment_version, course_id, subject_id, event_type,
            file_path, category, label, message, client_timestamp, client_timezone):
        # Database logging
        log = Log(assignment_id=assignment_id, assignment_version=assignment_version,
                  course_id=course_id,
                  subject_id=subject_id, file_path=file_path, event_type=event_type,
                  category=category, label=label, message=message.replace("\0", ""),
                  client_timestamp=client_timestamp,
                  client_timezone=client_timezone)
        db.session.add(log)
        db.session.commit()
        # Single-file logging
        logging.getLogger('Events').info(log.for_file())
        return log

    def __str__(self):
        return '<Log {} for {}>'.format(self.event, self.action)

    @staticmethod
    def calculate_feedbacks(assignment_id, course_id):
        return (db.session.query(func.count(Log.id))
                .filter(Log.assignment_id == assignment_id)
                .filter(Log.course_id == course_id)
                .filter(Log.event == 'feedback')
                .filter(Log.action != "Success")
                .group_by(Log.subject_id)
                .all())

    @staticmethod
    def get_logs_for_course(course_id):
        return Log.query.filter_by(course_id=course_id).all()

    @staticmethod
    def get_users_for_course(course_id):
        return (db.session.query(User)
                .filter(Log.course_id == course_id)
                .filter(Log.subject_id == User.id)
                .group_by(Log.subject_id, User)
                .all())

    @staticmethod
    def get_assignments_for_course(course_id) -> 'List[models.Assignment]':
        return (db.session.query(Assignment)
                .filter(Log.course_id == course_id)
                .filter(Log.assignment_id == Assignment.id)
                .group_by(Log.assignment_id, Assignment)
                .all())

    @staticmethod
    def get_history(course_id, assignment_id, user_id, page_offset=None, page_limit=None):
        logs = (
            Log.query.filter_by(
                course_id=course_id,
                assignment_id=assignment_id,
                subject_id=user_id
            ).order_by(Log.date_created.desc())
        )
        if page_offset is not None:
            logs.offset(page_offset)
        if page_limit is not None:
            logs.limit(page_limit)
        return [log.encode_json() for log in logs.all()]

    def for_file(self):
        return ", ".join((
            datetime_to_string(self.date_created),
            str(self.assignment_id),
            str(self.assignment_version),
            str(self.course_id),
            str(self.subject_id),
            json.dumps(self.file_path),
            json.dumps(self.event_type),
            json.dumps(self.category),
            json.dumps(self.label),
            json.dumps(self.message),
            json.dumps(self.client_timestamp),
            json.dumps(self.client_timezone)
        ))
