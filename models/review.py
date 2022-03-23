import os
import time

import base64

from flask import url_for
from sqlalchemy import Column, Text, Integer, Boolean, ForeignKey, Index, func, String

import models
from models.generics.models import db, ma
from models.generics.base import Base
from common.dates import datetime_to_string, string_to_datetime
from common.databases import optional_encoded_field
from common.filesystem import ensure_dirs


class Review(Base):
    comment = Column(Text(), default="")
    location = Column(Text(), default="")
    generic = Column(Boolean(), default=False)
    tag_id = Column(Integer(), ForeignKey('assignment_tag.id'), nullable=True)
    # Should be treated as out of X/100
    score = Column(Integer(), nullable=True)
    # Tracking
    submission_id = Column(Integer(), ForeignKey('submission.id'), nullable=True)
    author_id = Column(Integer(), ForeignKey('user.id'))
    assignment_version = Column(Integer(), default=0)
    submission_version = Column(Integer(), default=0)
    version = Column(Integer(), default=0)
    forked_id = Column(Integer(), ForeignKey('review.id'), nullable=True)
    forked_version = Column(Integer(), nullable=True)

    tag = db.relationship("AssignmentTag")
    submission = db.relationship("Submission")
    author = db.relationship("User")
    forked = db.relationship("Review")

    def __str__(self):
        return "<Review {} for {}>".format(self.id, self.submission_id)

    def encode_json(self):
        return {
            '_schema_version': 2,
            'id': self.id,
            'date_modified': self.date_modified,
            'date_created': self.date_created,
            'comment': self.comment,
            'location': self.location,
            'generic': self.generic,
            'tag_id': self.tag_id,
            'score': self.score,
            'submission_id': self.submission_id,
            'author_id': self.author_id,
            'assignment_version': self.assignment_version,
            'submission_version': self.submission_version,
            'version': self.version,
            'forked_id': self.forked_id,
            'forked_version': self.forked_version
        }

    @staticmethod
    def new(data):
        new_review = Review(comment=data['comment'],
                            location=data['location'],
                            generic=data['generic'].lower() == 'true',
                            tag_id=(data['tag_id']),
                            score=data['score'],
                            submission_id=int(data['submission_id']),
                            author_id=int(data['author_id']),
                            assignment_version=data['assignment_version'],
                            submission_version=data['submission_version'],
                            version=0,
                            forked_id=(data['forked_id']),
                            forked_version=0) #TODO: Handle forked_version
        db.session.add(new_review)
        db.session.commit()
        return new_review

    EDITABLE_SETTINGS = ('comment', 'location', 'score', 'generic',
                         'tag_id', 'forked_id', 'forked_version')

    def edit(self, data):
        changes = False
        for key in self.EDITABLE_SETTINGS:
            if key in data:
                old = getattr(self, key)
                new = data[key]
                setattr(self, key, new)
                changes = changes or (old != new)
        if changes:
            self.version += 1
        db.session.commit()
        return self

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    @staticmethod
    def get_for_submission(submission_id):
        return Review.query.filter_by(submission_id=submission_id).all()

    @staticmethod
    def get_generic_reviews():
        return Review.query.filter_by(generic=True).all()

    def get_actual_score(self):
        if self.score is not None:
            return self.score
        elif self.forked_id is None:
            return 0
        else:
            forked = Review.query.get(self.forked_id)
            if forked is None:
                return 0
            else:
                return forked.get_actual_score()



class ReviewSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Review
        include_fk = True
