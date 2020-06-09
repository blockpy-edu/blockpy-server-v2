"""
Membership table between Assignment Tags and Assignments
"""
from sqlalchemy import (Integer, Column, DateTime, func, ForeignKey, Table)
from models.base import Base

assignment_tag_membership = Table('assignment_tag_membership', Base.metadata,
                                  Column('assignment_id', Integer, ForeignKey('assignment.id')),
                                  Column('tag_id', Integer, ForeignKey('assignment_tag.id'))
                                  )