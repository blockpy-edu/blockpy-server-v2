"""
Membership table between Assignment Tags and Assignments
"""
from sqlalchemy import (Integer, Column, ForeignKey, Table)
from models.generics.models import ma
from models.generics.base import Base

assignment_tag_membership = Table('assignment_tag_membership', Base.metadata,
                                  Column('assignment_id', Integer, ForeignKey('assignment.id')),
                                  Column('tag_id', Integer, ForeignKey('assignment_tag.id'))
                                  )


class AssignmentTagMembershipSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = assignment_tag_membership
        include_fk = True
