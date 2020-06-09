from sqlalchemy import (event, Integer, Date, ForeignKey, Column, Table,
                        String, Boolean, DateTime, Text, ForeignKeyConstraint,
                        cast, func, and_, or_, Index)

from models.assignment import Assignment
from models.assignment_group import AssignmentGroup
from models.models import db
from models.base import Base
from common.dates import datetime_to_string, string_to_datetime
import models


class AssignmentGroupMembership(Base):
    __tablename__ = 'assignment_group_membership'
    assignment_group_id = Column(Integer(), ForeignKey('assignment_group.id'))
    assignment_id = Column(Integer(), ForeignKey('assignment.id'))
    position = Column(Integer())

    assignment_group = db.relationship("AssignmentGroup")
    assignment = db.relationship("Assignment")

    SCHEMA_V1_IGNORE_COLUMNS = Base.SCHEMA_V1_IGNORE_COLUMNS + ("assignment_group_url",
                                                                "assignment_url", "course_id")
    SCHEMA_V2_IGNORE_COLUMNS = Base.SCHEMA_V2_IGNORE_COLUMNS + ("assignment_group_url",
                                                                "assignment_url", "course_id")

    @classmethod
    def get_existing(cls, data):
        group_url = data['assignment_group_url']
        assignment_url = data['assignment_url']
        assignment = Assignment.by_url(assignment_url)
        group = AssignmentGroup.by_url(group_url)
        if not assignment or not group:
            return None
        return (AssignmentGroupMembership.query
                .filter_by(assignment_group_id=group.id,
                           assignment_id=assignment.id)
                .first())

    def __str__(self):
        return "<Membership {} in {}>".format(self.assignment_id, self.assignment_group_id)

    def encode_json(self):
        group = AssignmentGroup.by_id(self.assignment_group_id)
        group_url = group.url if group else None
        assignment = Assignment.by_id(self.assignment_id)
        assignment_url = assignment.url if assignment else None
        return {'_schema_version': 1,
                'assignment_group_id': self.assignment_group_id,
                'assignment_group_url': group_url,
                'assignment_id': self.assignment_id,
                'assignment_url': assignment_url,
                'position': self.position,
                'id': self.id,
                'date_modified': datetime_to_string(self.date_modified),
                'date_created': datetime_to_string(self.date_created)}

    @staticmethod
    def by_course(course_id):
        groups = [g.id for g in models.AssignmentGroup.by_course(course_id)]
        return (AssignmentGroupMembership
                .query
                .filter(AssignmentGroupMembership.assignment_group_id.in_(groups))
                .order_by(AssignmentGroupMembership.assignment_group_id,
                          AssignmentGroupMembership.assignment_id)
                .all())

    @staticmethod
    def move_assignment(assignment_id, new_group_id):
        membership = (AssignmentGroupMembership.query
                      .filter_by(assignment_id=assignment_id)
                      .first())
        if membership is None and new_group_id != -1:
            # -1 means delete
            membership = AssignmentGroupMembership(assignment_group_id=new_group_id,
                                                   assignment_id=assignment_id,
                                                   position=0)
            db.session.add(membership)
        elif new_group_id == -1:
            db.session.delete(membership)
        else:
            membership.assignment_group_id = new_group_id
        db.session.commit()
        return membership
