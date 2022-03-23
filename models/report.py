"""
Authentication information is used to make sure the user is valid.
"""
from sqlalchemy import Column, String, Integer, ForeignKey

from models.generics.models import ma
from models.generics.base import Base


class Report(Base):
    """
    Table for handling user authentication from various sources
    """
    title = Column(String())
    content = Column(String())


class ReportSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Report
        include_fk = True
