from sqlalchemy import Column, String, Integer, ForeignKey, Text, or_

import models
from models.models import db
from models.base import Base
from common.dates import datetime_to_string, string_to_datetime


class Course(Base):
    name = Column(String(255))
    url = Column(String(255), default=None, nullable=True)
    owner_id = Column(Integer(), ForeignKey('user.id'))
    SERVICES = ['native', 'lti']
    service = Column(String(80), default="native")
    external_id = Column(String(255), default="")
    endpoint = Column(Text(), default="")
    VISIBILITIES = ['private', 'public']
    visibility = Column(String(80), default="private")
    term = Column(String(255), default="")
    settings = Column(Text(), default="")

    owner = db.relationship("User")

    def encode_json(self):
        user = models.User.query.get(self.owner_id)
        return {'_schema_version': 3,
                'name': self.name,
                'url': self.url,
                'owner_id': self.owner_id,
                'owner_id__email': user.email if user else '',
                'service': self.service,
                'external_id': self.external_id,
                'endpoint': self.endpoint,
                'visibility': self.visibility,
                'settings': self.settings,
                'term': self.term,
                'id': self.id,
                'date_modified': datetime_to_string(self.date_modified),
                'date_created': datetime_to_string(self.date_created)}

    SCHEMA_V1_IGNORE_COLUMNS = Base.SCHEMA_V1_IGNORE_COLUMNS + ('owner_id__email',)
    SCHEMA_V2_IGNORE_COLUMNS = Base.SCHEMA_V2_IGNORE_COLUMNS + ('owner_id__email',)
    SCHEMA_V3_IGNORE_COLUMNS = SCHEMA_V2_IGNORE_COLUMNS


    @staticmethod
    def export(course_id):
        course = Course.query.get(course_id)
        # Get all course's assignments
        course_assignments = models.Assignment.by_course(course_id, False)
        # Get all course's assignment groups
        groups = course.get_assignment_groups()
        assignment_groups = [a.encode_json() for a in groups]

        # Get all assignment groups' memberships
        assignment_memberships = [a.encode_json()
                                  for a in models.AssignmentGroupMembership.by_course(course_id)]
        # Get all assignment groups' assignments
        groups_assignments = {a for g in groups
                              for a in g.get_assignments()}
        groups_assignments.update(course_assignments)
        assignments = [a.encode_json() for a in groups_assignments]
        assignments.sort(key=lambda a: a['name'])
        return {
            'course': course.encode_json(),
            'assignments': assignments,
            'assignment_groups': assignment_groups,
            'assignment_memberships': assignment_memberships
        }

    def __str__(self):
        return '<Course {}>'.format(self.id)

    @staticmethod
    def get_public():
        return Course.query.filter_by(visibility='public').all()

    @staticmethod
    def remove(course_id, remove_linked=False):
        Course.query.filter_by(id=course_id).delete()
        if remove_linked:
            for m in models.AssignmentGroupMembership.by_course(course_id):
                db.session.delete(m)
            for a in models.Assignment.by_course(course_id):
                for s in a.sample_submissions():
                    db.session.delete(s)
                db.session.delete(a)
            for g in models.AssignmentGroup.by_course(course_id):
                db.session.delete(g)
            for r in models.Role.by_course(course_id):
                db.session.delete(r)
        db.session.commit()

    def get_users(self):
        return (db.session.query(models.Role, models.User)
                .filter(models.Role.course_id == self.id)
                .filter(models.Role.user_id == models.User.id).all())

    def get_students(self):
        return [x[1] for x in (db.session.query(models.Role, models.User)
                               .filter(models.Role.course_id == self.id)
                               .filter(models.Role.user_id == models.User.id).distinct())]

    def get_assignments(self):
        return (db.session.query(models.Assignment, models.AssignmentGroupMembership)
                .filter(models.Assignment.course_id == self.id,
                        models.AssignmentGroupMembership.assignment_id == models.Assignment.id)
                .all())

    def get_submitted_assignments(self):
        return (db.session.query(models.Assignment)
                .join(models.Submission, models.Submission.assignment_id == models.Assignment.id)
                .filter(models.Submission.course_id == self.id)
                .distinct())

    def get_submissions(self):
        return (db.session.query(models.Submission)
                .filter(models.Submission.course_id == self.id)
                .all())

    def get_assignment_groups(self):
        return (db.session.query(models.AssignmentGroup)
                .filter(models.AssignmentGroup.course_id == self.id)
                .order_by(models.AssignmentGroup.name)
                .all())

    def update_endpoint(self, endpoint):
        self.endpoint = endpoint
        db.session.commit()

    @staticmethod
    def get_all_groups(menu='embed'):
        courses = Course.query.all()
        return [{'id': course.id,
                 'name': course.name,
                 'groups': [{'id': group.id,
                             'name': group.name,
                             'select_url': group.get_select_url(menu)}
                            for group in models.AssignmentGroup.by_course(course.id)]
                 }
                for course in courses]

    @staticmethod
    def rename(course_id, name=None):
        course = Course.by_id(course_id)
        if name is not None:
            course.name = name
        db.session.commit()
        return course

    @staticmethod
    def new(name, owner_id, visibility):
        if visibility == 'public':
            visibility = 'public'
        else:
            visibility = 'private'
        new_course = Course(name=name, owner_id=owner_id, visibility=visibility)
        db.session.add(new_course)
        db.session.flush()
        new_role = models.Role(name='instructor', user_id=owner_id, course_id=new_course.id)
        db.session.add(new_role)
        db.session.commit()
        return new_course

    @staticmethod
    def new_lti_course(service, external_id, name, user_id, endpoint=""):
        new_course = Course(name=name, owner_id=user_id,
                            service=service, external_id=external_id,
                            endpoint=endpoint)
        db.session.add(new_course)
        db.session.commit()
        return new_course

    @staticmethod
    def by_url(course_url):
        return Course.query.filter_by(url=course_url).first()

    @staticmethod
    def from_lti(service, lti_context_id, name, user_id, endpoint=""):
        lti_course = Course.query.filter_by(external_id=lti_context_id).first()
        if lti_course is None:
            return Course.new_lti_course(service=service,
                                         external_id=lti_context_id,
                                         name=name,
                                         user_id=user_id,
                                         endpoint=endpoint)
        else:
            return lti_course

    def grading_grid(self):
        # Return a list of lists of assignments/students/submissions
        assignments = []
        submissions = []
        return assignments, submissions
