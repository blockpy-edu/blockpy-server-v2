from typing import List

from flask import g
from controllers.setup import registry, rebar, generator
from models.course import CourseSchema


cs = {'acbart@vt.edu': [{'name': 'CISC108'}, {'name': 'CISC275'}]}


@registry.handles(rule='/courses', method='GET', response_body_schema=CourseSchema(many=True))
def courses() -> List[CourseSchema]:
    if g.user['email'] == 'acbart@vt.edu':
        return cs[g.user['email']]
    else:
        return cs.get(g.user['email'], [])


@registry.handles(rule='/course', method='POST', response_body_schema=CourseSchema)
def new_course():
    if g.user['email'] not in cs:
        cs[g.user['email']] = []
    cs[g.user['email']].append(({'name': "OOH FANCY"}))
