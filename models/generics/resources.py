"""
A Resource is a base class with other stuff bolted on
"""
from sqlalchemy import Column, String, Integer, ForeignKey, Text, or_, Boolean


class Resource:
    pass


class WithUrl:
    id: int
    url = Column(String(255), default=None, nullable=True)

    def identify(self):
        return f"url={self.url}" if self.url else f"id={self.id}"


class WithVersion:
    version = Column(Integer(), default=0)


VISIBILITIES = ['private', 'public', 'students', 'teacher']


class WithVisibility:
    VISIBILITIES = ['private', 'public', 'students', 'teacher']

