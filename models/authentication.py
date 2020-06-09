"""
Authentication information is used to make sure the user is valid.
"""
from sqlalchemy import Column, String, Integer, ForeignKey

from models.base import Base


class Authentication(Base):
    """
    Table for handling user authentication from various sources
    """
    type = Column(String(80))
    value = Column(String(255))
    user_id = Column(Integer(), ForeignKey('user.id'))

    TYPES = ['local', 'canvas']

    def __str__(self):
        return '<{} is {}>'.format(self.type, self.user_id)
