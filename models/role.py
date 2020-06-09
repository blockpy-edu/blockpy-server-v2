from flask_security import RoleMixin
from sqlalchemy import Column, String, Integer, ForeignKey

from models.models import db
from models.base import Base


class Role(Base, RoleMixin):
    name = Column(String(80))
    user_id = Column(Integer(), ForeignKey('user.id'))
    course_id = Column(Integer(), ForeignKey('course.id'), default=None)

    course = db.relationship("Course")

    NAMES = ['instructor', 'admin', 'student']

    def update_role(self, new_role):
        pass

    def __str__(self):
        return '<User {} is {}>'.format(self.user_id, self.name)

    @staticmethod
    def remove(role_id):
        Role.query.filter_by(id=role_id).delete()
        db.session.commit()

    @staticmethod
    def by_course(course_id):
        return Role.query.filter_by(course_id=course_id).all()
