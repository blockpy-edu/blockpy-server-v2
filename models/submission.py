import json
import os
import time

import base64

from flask import url_for
from sqlalchemy import Column, Text, Integer, Boolean, ForeignKey, Index, func, String, or_
from sqlalchemy.orm import relationship

import models
from models.assignment import Assignment
from models.log import Log
from models.generics.models import db, ma
from models.generics.base import Base
from common.dates import datetime_to_string
from common.databases import optional_encoded_field
from common.filesystem import ensure_dirs
from models.review import Review


class SubmissionStatuses:
    # Not yet begun - the value if the submission does not exist
    INITIALIZED = "Initialized"
    # Started -> not yet run
    STARTED = "Started"
    # inProgress -> Run, but not yet marked formally as "submitted"
    IN_PROGRESS = "inProgress"
    # Submitted -> formally marked
    SUBMITTED = "Submitted"
    # Completed -> Either formally Submitted and FullyGraded, or auto graded as "correct"
    COMPLETED = "Completed"

    VALID_CHOICES = (STARTED, IN_PROGRESS, SUBMITTED, COMPLETED)


class GradingStatuses:
    FULLY_GRADED = 'FullyGraded'
    PENDING = 'Pending'
    PENDING_MANUAL = 'PendingManual'
    FAILED = 'Failed'
    NOT_READY = 'NotReady'

    VALID_CHOICES = (FULLY_GRADED, PENDING, PENDING_MANUAL, FAILED, NOT_READY)


class Submission(Base):
    code = Column(Text(), default="")
    extra_files = Column(Text(), default="")
    url = Column(Text(), default="")
    endpoint = Column(Text(), default="")
    # Should be treated as out of X/100
    score = Column(Integer(), default=0)
    correct = Column(Boolean(), default=False)
    submission_status = Column(String(255), default=SubmissionStatuses.STARTED)
    grading_status = Column(String(255), default=GradingStatuses.NOT_READY)
    # Tracking
    assignment_id = Column(Integer(), ForeignKey('assignment.id'))
    assignment_group_id = Column(Integer(), ForeignKey('assignment_group.id'), nullable=True)
    course_id = Column(Integer(), ForeignKey('course.id'))
    user_id = Column(Integer(), ForeignKey('user.id'))
    assignment_version = Column(Integer(), default=0)
    version = Column(Integer(), default=0)

    assignment = relationship("Assignment")
    assignment_group = relationship("AssignmentGroup")
    course = relationship("Course")
    user = relationship("User")

    __table_args__ = (Index('submission_index', "assignment_id",
                            "course_id", "user_id"),)

    def encode_json(self, use_owner=True):
        return {
            '_schema_version': 2,
            'code': self.code,
            'extra_files': self.extra_files,
            'url': self.url,
            'endpoint': self.endpoint,
            'score': self.score,
            'correct': self.correct,
            'assignment_id': self.assignment_id,
            'course_id': self.course_id,
            'user_id': self.user_id,
            'assignment_version': self.assignment_version,
            'version': self.version,
            'submission_status': self.submission_status,
            'grading_status': self.grading_status,
            'user_id__email': optional_encoded_field(self.user_id, use_owner, models.User.query.get, 'email'),
            'id': self.id,
            'date_modified': datetime_to_string(self.date_modified),
            'date_created': datetime_to_string(self.date_created)
        }

    def encode_human(self):
        try:
            extra_files = json.loads(self.extra_files)
            if isinstance(extra_files, dict):
                extra_files = {k:v for k,v in extra_files.items()}
            else:
                extra_files = {f['filename']: f['contents'] for f in extra_files}
        except json.JSONDecodeError:
            extra_files = {}
        files = {
            'answer.py': self.code,
            '_grade.json': json.dumps({
                'score': self.score,
                'correct': self.correct,
                'submission_status': self.submission_status,
                'grading_status': self.grading_status,
                'assignment_id': self.assignment_id,
                'id': self.id,
                'course_id': self.course_id,
                'user_id': self.user_id,
                'assignment_version': self.assignment_version,
                'version': self.version,
                'files': ['answer.py']+[f[0] for f in extra_files]
            }),
            **extra_files
        }
        return files

    @staticmethod
    def full_by_id(submission_id):
        result = (db.session.query(Submission, models.User, models.Assignment)
                  .filter(Submission.user_id == models.User.id)
                  .filter(Submission.assignment_id == models.Assignment.id)
                  .filter(Submission.id == submission_id)
                  .first())
        if result is None:
            return None, None, None
        else:
            return result

    @staticmethod
    def by_assignment(assignment_id, course_id):
        return (db.session.query(Submission, models.User, models.Assignment)
                .filter(Submission.user_id == models.User.id)
                .filter(Submission.assignment_id == models.Assignment.id)
                .filter(Submission.assignment_id == assignment_id)
                .filter(Submission.course_id == course_id)
                .all())

    @staticmethod
    def get_latest(assignment_id, course_id):
        return (db.session.query(func.max(Submission.date_modified))
                .filter(Submission.course_id == course_id,
                        Submission.assignment_id == assignment_id)
                .group_by(Submission.user_id)
                .order_by(func.max(Submission.date_modified).desc())
                .count())

    @staticmethod
    def by_student(user_id, course_id):
        return (db.session.query(Submission, models.User, models.Assignment)
                .filter(Submission.user_id == models.User.id)
                .filter(Submission.assignment_id == models.Assignment.id)
                .filter(Submission.user_id == user_id)
                .filter(Submission.course_id == course_id)
                .all())

    @staticmethod
    def by_pending_review(course_id):
        return (db.session.query(Submission, models.User, models.Assignment)
                .filter(or_(Submission.submission_status == SubmissionStatuses.SUBMITTED,
                            Submission.submission_status == SubmissionStatuses.COMPLETED))
                .filter(or_(Submission.grading_status == GradingStatuses.PENDING_MANUAL,
                            Submission.grading_status == GradingStatuses.NOT_READY))
                .filter(Submission.user_id == models.User.id)
                .filter(Submission.assignment_id == models.Assignment.id)
                .filter(models.Assignment.reviewed)
                .filter(Submission.course_id == course_id)
                .order_by(models.Assignment.name.asc(),
                          models.User.last_name.asc(),
                          models.User.first_name.asc())
                .all())

    def __str__(self):
        return '<Submission {} for {}>'.format(self.id, self.user_id)

    def full_status(self, allow_hide=True):
        if allow_hide and self.assignment.hidden:
            return "????"
        elif self.correct:
            return "Complete"
        elif self.assignment.reviewed:
            if self.grading_status == "PendingManual":
                return "Pending review"
            else:
                return self.submission_status
        elif self.score:
            return "Incomplete ({}%)".format(self.score)
        else:
            return "Incomplete"

    def full_score(self):
        if self.assignment.reviewed:
            review_score = self.get_reviewed_scores()
            return (self.score + review_score) / 100.0
        return float(self.correct) or self.score / 100.0


    def get_reviewed_scores(self):
        reviews = Review.query.filter_by(submission_id=self.id).all()
        total = 0
        for review in reviews:
            total += review.get_actual_score()
        return total


    @staticmethod
    def from_assignment(assignment, user_id, course_id, assignment_group_id=None) -> 'Submission':
        submission = Submission(assignment_id=assignment.id,
                                user_id=user_id,
                                assignment_group_id=assignment_group_id,
                                course_id=course_id,
                                code=assignment.starting_code,
                                extra_files=assignment.extra_starting_files,
                                assignment_version=assignment.version)
        db.session.add(submission)
        db.session.commit()
        # TODO: Log extra starting files!
        Log.new(assignment.id, assignment.version, course_id, user_id,
                "File.Create", "answer.py", "", "", assignment.starting_code, "", "")
        return submission

    @staticmethod
    def get_submission(assignment_id, user_id, course_id):
        return Submission.query.filter_by(assignment_id=assignment_id,
                                          course_id=course_id,
                                          user_id=user_id).first()

    @staticmethod
    def load_or_new(assignment, user_id, course_id, new_submission_url="", assignment_group_id=None):
        submission = Submission.get_submission(assignment.id, user_id, course_id)
        if not submission:
            submission = Submission.from_assignment(assignment, user_id, course_id, assignment_group_id)

        if new_submission_url:
            submission.endpoint = new_submission_url
            db.session.commit()
        return submission

    STUDENT_FILENAMES = ("#extra_student_files.blockpy", "answer.py")

    def save_code(self, filename, code):
        if filename == "#extra_student_files.blockpy":
            self.extra_files = code
        elif filename == "answer.py":
            self.code = code
        self.version += 1
        self.assignment_version = self.assignment.version
        db.session.commit()

    def set_submission(self, score, correct):
        self.score = score
        self.correct = correct
        self.grading_status = GradingStatuses.FULLY_GRADED
        db.session.commit()

    def update_submission(self, score, correct):
        was_changed = self.score != score or self.correct != correct
        self.score = score
        self.correct = correct
        assignment = Assignment.by_id(self.assignment_id)
        if assignment.reviewed:
            self.submission_status = SubmissionStatuses.IN_PROGRESS
            self.grading_status = GradingStatuses.NOT_READY
        elif self.correct:
            self.submission_status = SubmissionStatuses.COMPLETED
            self.grading_status = GradingStatuses.FULLY_GRADED
        else:
            self.submission_status = SubmissionStatuses.SUBMITTED
            self.grading_status = GradingStatuses.PENDING
        db.session.commit()
        return was_changed

    def update_submission_status(self, status):
        if status not in SubmissionStatuses.VALID_CHOICES:
            return False
        self.submission_status = status
        db.session.commit()
        return True

    def update_grading_status(self, status):
        if status not in GradingStatuses.VALID_CHOICES:
            return False
        self.grading_status = status
        db.session.commit()
        return True

    @staticmethod
    def save_correct(user_id, assignment_id, course_id):
        submission = Submission.query.filter_by(user_id=user_id,
                                                assignment_id=assignment_id,
                                                course_id=course_id).first()
        if not submission:
            submission = Submission(assignment_id=assignment_id,
                                    user_id=user_id,
                                    course_id=course_id,
                                    correct=True)
            db.session.add(submission)
        else:
            submission.correct = True
        db.session.commit()
        return submission

    def set_status(self, new_value):
        was_changed = self.status != new_value
        self.status = new_value
        db.session.commit()
        return was_changed

    def get_report_blockpy(self, image=""):
        if self.correct:
            message = "Success!"
        else:
            message = "Incomplete"

    def get_block_image(self):
        return self.get_image('submission_blocks', 'blockpy.get_submission_image')

    def get_image(self, directory, endpoint='blockpy.get_image'):
        sub_blocks_folder = os.path.join(app.config['UPLOADS_DIR'], directory)
        image_path = os.path.join(sub_blocks_folder, str(self.id) + '.png')
        if os.path.exists(image_path):
            return url_for(endpoint, submission_id=self.id, directory=directory, _external=True)
        return ""

    def save_block_image(self, image=""):
        return self.save_image('submission_blocks', image, 'blockpy.get_submission_image')

    def save_image(self, directory, data, endpoint='blockpy.get_image'):
        sub_folder = os.path.join(app.config['UPLOADS_DIR'], directory)
        image_path = os.path.join(sub_folder, str(self.id) + '.png')
        if data != "":
            converted_image = base64.b64decode(data[22:])
            with open(image_path, 'wb') as image_file:
                image_file.write(converted_image)
            return url_for(endpoint, submission_id=self.id, _external=True)
        elif os.path.exists(image_path):
            try:
                os.remove(image_path)
            except Exception as e:
                app.logger.info("Could not delete because:" + str(e))
        return None

    def log_code(self, course_id, extension='.py', timestamp=''):
        '''
        Store the code on disk, mapped to the Assignment ID and the Student ID
        '''
        # Multiple-file logging
        log = models.Log.new('code', 'set', self.assignment_id, self.assignment_version,
                             course_id,
                             self.user_id, body=self.code, timestamp=timestamp)

        directory = os.path.join(app.config['BLOCKPY_LOG_DIR'],
                                 str(self.assignment_id),
                                 str(self.user_id))

        ensure_dirs(directory)
        name = time.strftime("%Y%m%d-%H%M%S")
        file_name = os.path.join(directory, name + extension)

        with open(file_name, 'w') as blockly_logfile:
            blockly_logfile.write(self.code)

    def get_reviews(self):
        return [review.encode_json() for review in
                Review.query.filter_by(submission_id=self.id).all()]

    @staticmethod
    def get_meta_reviews():
        return [review.encode_json() for review in
                Review.query.filter_by(generic=True).all()]


class SubmissionSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Submission
        include_fk = True
