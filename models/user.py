from flask_security import UserMixin
from sqlalchemy import Column, Integer, String, Boolean, DateTime, func

import models
from models.models import db, ma
from models.base import Base


class User(Base, UserMixin):
    # General user properties
    id = Column(Integer(), primary_key=True)
    first_name = Column(String(255))
    last_name = Column(String(255))

    email = Column(String(255))

    proof = Column(String(255), default='')
    password = Column(String(255))
    active = Column(Boolean())
    confirmed_at = Column(DateTime())

    # Foreign key relationships
    #roles = db.relationship("Role", backref='user', lazy='dynamic')
    #authentications = db.relationship("Authentication", backref='user', lazy='dynamic')
    #assignments = db.relationship("Assignment", backref='user', lazy='dynamic')

    STAFF_ROLES = ["urn:lti:role:ims/lis/teachingassistant",
                   "instructor", "contentdeveloper", "teachingassistant",
                   "urn:lti:role:ims/lis/instructor",
                   "urn:lti:role:ims/lis/contentdeveloper"]

    def encode_json(self, use_owner=True):
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email
        }

    @staticmethod
    def new_from_instructor(email, first_name='', last_name=''):
        new_user = User(first_name=first_name, last_name=last_name,
                        email=email)
        db.session.add(new_user)
        db.session.commit()
        return new_user

    @staticmethod
    def find_student(email):
        # Hack: We have to lowercase emails because apparently some LMSes want to SHOUT EMAIL ADDRESSES
        return User.query.filter(func.lower(User.email) == func.lower(email)).first()

    def get_roles(self):
        return models.Role.query.filter_by(user_id=self.id).all()

    def get_course_roles(self, course_id):
        return models.Role.query.filter_by(user_id=self.id, course_id=course_id).all()

    def get_editable_courses(self):
        return (db.session.query(models.Course)
                .filter(models.Role.user_id == self.id,
                        models.Role.course_id == models.Course.id,
                        (models.Role.name == 'instructor')
                        | (models.Role.name == 'admin'))
                .order_by(models.Course.name)
                .distinct())

    def get_courses(self):
        return (db.session.query(models.Course, models.Role)
                .filter(models.Role.user_id == self.id,
                        models.Role.course_id == models.Course.id)
                .order_by(models.Role.name)
                .all())

    def __str__(self):
        return '<User {} ({})>'.format(self.id, self.email)

    def name(self):
        return ' '.join((self.first_name, self.last_name))

    def in_course(self, course_id):
        return bool(models.Role.query.filter_by(course_id=course_id, user_id=self.id).first())

    def is_admin(self):
        return 'admin' in {role.name.lower() for role in self.roles.all()}

    def is_instructor(self, course_id=None):
        if course_id is not None:
            return 'instructor' in {role.name.lower() for role in self.roles.all()
                                    if role.course_id == course_id}
        return 'instructor' in {role.name.lower() for role in self.roles.all()}

    def is_grader(self, course_id=None):
        if course_id is not None:
            role_strings = {role.name.lower() for role in self.roles.all()
                            if role.course_id == course_id}
        else:
            role_strings = {role.name.lower() for role in self.roles.all()}
        return ('instructor' in role_strings or
                'urn:lti:sysrole:ims/lis/none' in role_strings or
                'urn:lti:role:ims/lis/teachingassistant' in role_strings)

    def is_student(self, course_id=None):
        if course_id is not None:
            return 'learner' in {role.name.lower() for role in self.roles.all()
                                 if role.course_id == course_id}
        return 'learner' in {role.name.lower() for role in self.roles.all()}

    def add_role(self, name, course_id):
        new_role = models.Role(name=name, user_id=self.id, course_id=course_id)
        db.session.add(new_role)
        db.session.commit()

    def update_roles(self, new_roles, course_id):
        old_roles = [role for role in self.roles.all() if role.course_id == course_id]
        new_role_names = set(new_role_name.lower() for new_role_name in new_roles)
        for old_role in old_roles:
            if old_role.name.lower() not in new_role_names:
                models.Role.query.filter(models.Role.id == old_role.id).delete()
        old_role_names = set(role.name.lower() for role in old_roles)
        for new_role_name in new_roles:
            if new_role_name.lower() not in old_role_names:
                new_role = models.Role(name=new_role_name.lower(), user_id=self.id, course_id=course_id)
                db.session.add(new_role)
        db.session.commit()

    def determine_role(self, assignments, submissions):
        '''
        Note that when you use an assignment from another course, you are implicitly giving all the
        graders from that course access to your students' submissions in the editor menu. Of course,
        it would be very unusual to be able to access submissions from that menu, but in theory that's
        what this role delegation means.

        :param assignments:
        :param submissions:
        :return:
        '''
        role = 'student'
        if assignments and self.is_grader(assignments[0].course_id):
            role = 'owner'
        elif submissions and self.is_grader(submissions[0].course_id):
            role = 'grader'
        return role

    @staticmethod
    def is_lti_instructor(given_roles):
        return any(role.lower() for role in User.STAFF_ROLES if role in given_roles)

    @staticmethod
    def new_lti_user(service, lti_user_id, lti_email, lti_first_name, lti_last_name):
        new_user = User(first_name=lti_first_name, last_name=lti_last_name, email=lti_email.lower(),
                        password="", active=True, confirmed_at=None)
        db.session.add(new_user)
        db.session.flush()
        new_authentication = models.Authentication(type=service,
                                                   value=lti_user_id,
                                                   user_id=new_user.id)
        db.session.add(new_authentication)
        db.session.commit()
        return new_user

    def register_authentication(self, service, lti_user_id):
        new_authentication = models.Authentication(type=service,
                                                   value=lti_user_id,
                                                   user_id=self.id)
        db.session.add(new_authentication)
        db.session.commit()
        return self

    @staticmethod
    def from_lti(service, lti_user_id, lti_email, lti_first_name, lti_last_name):
        """
        For a given service (e.g., "canvas"), and a user_id in the LTI system
        """
        lti = models.Authentication.query.filter_by(type=service,
                                                    value=lti_user_id).first()
        if lti is None:
            user = User.find_student(lti_email)
            if user:
                user.register_authentication(service, lti_user_id)
                return user
            else:
                return User.new_lti_user(service, lti_user_id, lti_email, lti_first_name, lti_last_name)
        else:
            return lti.user


class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        # include_fk = True
        #load_instance = True
