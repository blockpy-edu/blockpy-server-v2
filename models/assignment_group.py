from flask import url_for
from sqlalchemy import Column, String, Integer, ForeignKey, func
from natsort import natsorted
from werkzeug.utils import secure_filename

import models
from models.generics.models import db, ma
from models.generics.base import Base
from common.dates import datetime_to_string
from typing import List


class AssignmentGroup(Base):
    __tablename__ = 'assignment_group'
    name = Column(String(255), default="Untitled")
    url = Column(String(255), nullable=True)
    forked_id = Column(Integer(), ForeignKey('assignment_group.id'), nullable=True)
    forked_version = Column(Integer(), nullable=True)
    owner_id = Column(Integer(), ForeignKey('user.id'))
    course_id = Column(Integer(), ForeignKey('course.id'))
    position = Column(Integer(), default=0)
    version = Column(Integer(), default=0)

    forked = db.relationship("AssignmentGroup")
    owner = db.relationship("User")
    course = db.relationship("Course")

    def __str__(self):
        return '<Group {} in {} ({})>'.format(self.name, self.course_id, self.url)

    def encode_json(self):
        user = models.User.query.get(self.owner_id)
        return {'_schema_version': 2,
                'name': self.name,
                'url': self.url,
                'forked_id': self.forked_id,
                'forked_version': self.forked_version,
                'owner_id': self.owner_id,
                'owner_id__email': user.email if user else '',
                'course_id': self.course_id,
                'position': self.position,
                'id': self.id,
                'date_modified': datetime_to_string(self.date_modified),
                'date_created': datetime_to_string(self.date_created)}

    SCHEMA_V1_IGNORE_COLUMNS = Base.SCHEMA_V1_IGNORE_COLUMNS + ('owner_id__email',)
    SCHEMA_V2_IGNORE_COLUMNS = Base.SCHEMA_V2_IGNORE_COLUMNS + ('owner_id__email',)

    @staticmethod
    def new(owner_id, course_id, name="Untitled Group"):
        last = (db.session.query(func.max(AssignmentGroup.position).label("last_position"))
                .filter_by(course_id=course_id).one()).last_position
        assignment_group = AssignmentGroup(owner_id=owner_id, course_id=course_id,
                                           name=name,
                                           position=last + 1 if last else 1)
        db.session.add(assignment_group)
        db.session.commit()
        return assignment_group

    @staticmethod
    def remove(assignment_group_id):
        # Reorder existing
        group = AssignmentGroup.query.filter_by(id=assignment_group_id).one()
        position = group.position
        all_groups = (AssignmentGroup.query
                      .filter(AssignmentGroup.course_id == group.course_id,
                              AssignmentGroup.position > position)
                      .update({"position": (AssignmentGroup.position - 1)}))
        # Delete target
        AssignmentGroup.query.filter_by(id=assignment_group_id).delete()
        models.AssignmentGroupMembership.query.filter_by(assignment_group_id=assignment_group_id).delete()
        db.session.commit()

    @staticmethod
    def is_in_course(assignment_group_id, course_id):
        return AssignmentGroup.query.get(assignment_group_id).course_id == course_id

    @staticmethod
    def id_by_url(assignment_group_url):
        if assignment_group_url is None:
            return None
        possible = AssignmentGroup.query.filter_by(url=assignment_group_url).first()
        if possible:
            return possible.id
        return None

    @staticmethod
    def by_url(assignment_group_url):
        if assignment_group_url is None:
            return None
        possible = AssignmentGroup.query.filter_by(url=assignment_group_url).first()
        return possible

    @staticmethod
    def by_course(course_id):
        return (AssignmentGroup.query.filter_by(course_id=course_id)
                .order_by(AssignmentGroup.name)
                .all())

    @staticmethod
    def by_assignment(assignment_id):
        return (AssignmentGroup.query
                .filter(AssignmentGroup.id == models.AssignmentGroupMembership.assignment_group_id,
                        models.AssignmentGroupMembership.assignment_id == assignment_id,
                        models.Assignment.id == assignment_id)
                .order_by(AssignmentGroup.course_id == models.Assignment.course_id)
                .all())

    @staticmethod
    def get_ungrouped_assignments(course_id):
        return (models.Assignment.query
                .filter_by(course_id=course_id)
                .outerjoin(models.AssignmentGroupMembership)
                .filter(models.AssignmentGroupMembership.assignment_id == None)
                .all())

    def get_assignments(self) -> 'List[models.Assignment]':
        assignments = (models.Assignment.query
                .join(models.AssignmentGroupMembership,
                      models.AssignmentGroupMembership.assignment_id == models.Assignment.id)
                .filter(models.AssignmentGroupMembership.assignment_group_id == self.id)
                .order_by(models.Assignment.name, models.AssignmentGroupMembership.position)
                .all())
        return natsorted(assignments, key=lambda a: a.title())

    def get_memberships(self):
        return (models.AssignmentGroupMembership.query
                       .filter(models.AssignmentGroupMembership.assignment_group_id == self.id)
                       .order_by(models.AssignmentGroupMembership.position,
                                 models.AssignmentGroupMembership.id)
                       .all())

    def get_select_url(self, menu):
        # TODO: Refactor web logic outside of model?
        if self.url:
            return url_for('assignments.load', assignment_group_url=self.url, _external=True, embed=menu == 'embed')
        return url_for('assignments.load', assignment_group_id=self.id, _external=True, embed=menu == 'embed')

    def get_filename(self):
        if self.url:
            return secure_filename(self.url) + ".json"
        else:
            return secure_filename(self.name) + ".json"




class GroupSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = AssignmentGroup
        include_fk = True
