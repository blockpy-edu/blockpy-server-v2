"""
Authentication information is used to make sure the user is valid.
"""
from sqlalchemy import Column, String, Integer, ForeignKey

from models.generics.models import ma
from models.generics.base import Base


class Grader(Base):
    """
    Table for handling user authentication from various sources
    """
    course_id = Column(Integer(), ForeignKey('course.id'))
    student_id = Column(Integer(), ForeignKey('user.id'))
    grader_id = Column(Integer(), ForeignKey('user.id'))
    relationship = Column(String(), default='grader')

    def __str__(self):
        return '<{} is {}>'.format(self.type, self.user_id)


class GraderSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Grader
        include_fk = True
