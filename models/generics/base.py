"""
The base model that all other models inherit from
"""
import json
from typing import Tuple, Dict, Optional

from sqlalchemy import (Integer, Column, DateTime, func)
from sqlalchemy.ext.declarative import declared_attr

from common.dates import string_to_datetime, datetime_to_pretty_string
from models.generics.models import db, ma


class Base(db.Model):
    """
    Base Schema of all database models for the site. Everything inherits from
    this schema.
    """
    # No one should instantiate this directly
    __abstract__ = True

    id = Column(Integer(), primary_key=True, autoincrement=True)
    date_created = Column(DateTime, default=func.current_timestamp())
    date_modified = Column(DateTime, default=func.current_timestamp(),
                           onupdate=func.current_timestamp())

    SCHEMA_V1_IGNORE_COLUMNS = ('id', 'date_modified')
    SCHEMA_V2_IGNORE_COLUMNS = SCHEMA_V1_IGNORE_COLUMNS
    SCHEMA_V1_RENAME_COLUMNS = {}
    SCHEMA_V2_RENAME_COLUMNS = {}

    @classmethod
    def get_schema(cls, schema_version: int) -> (Tuple[str], Dict[str, str]):
        """
        Given the `schema_version`, provide the appropriate columns to ignore
        and rename. This gives us a simplistic mechanism to handle data versioning.

        It would have been nice to have this as a dictionary, but inheriting dictionaries
        and setting their keys is a tricky thing.

        :param schema_version: Which version of the schema to provide
        :return: The IGNORE and RENAME columns
        """
        if schema_version == 1:
            return cls.SCHEMA_V1_IGNORE_COLUMNS, cls.SCHEMA_V1_RENAME_COLUMNS
        elif schema_version == 2:
            return cls.SCHEMA_V2_IGNORE_COLUMNS, cls.SCHEMA_V2_RENAME_COLUMNS
        raise Exception("Unknown schema version: {}".format(schema_version))

    @declared_attr
    def __tablename__(self) -> str:
        """
        Creates a class-level field named `__tablename__` available that is
        the name of the table in the database. This is actually just the
        lower-case version of the class name.
        :return: The name of the table
        """
        return self.__name__.lower()

    def __repr__(self) -> str:
        """
        Create a string representation of this schema.
        :return: String representation of this model.
        """
        return str(self)

    def pretty_date_modified(self) -> str:
        """
        Get a human-readable version of this object's last modified date.
        :return: A string
        """
        return datetime_to_pretty_string(self.date_modified)

    def pretty_date_created(self) -> str:
        """
        Get a human-readable version of this object's created date.
        :return: A string
        """
        return datetime_to_pretty_string(self.date_created)

    @classmethod
    def decode_json(cls, data: dict, **kwargs) -> 'Base':
        """
        Default unmarshalling method for transforming the given JSON-formatted data
        into appropriate instance of a class. Additional keys and values can be
        passed in to `kwargs` to add/override the fields in `data`.
        :param data: A valid JSON dictionary with all the fields needed to construct
            an instance of this model.
        :param kwargs: Additional keys+values to add to the constructed model.
        :return: An instance of this model.
        """
        data = dict(data)
        schema_version = data.pop('_schema_version')
        ignored, renamed = cls.get_schema(schema_version)
        # Reformat the creation date to be a datetime object
        data['date_created'] = string_to_datetime(data['date_created'])
        # Rename keys as needed
        for old, new in renamed:
            data[new] = data.pop(old)
        # Copy over keys from the `kwargs`
        for key, value in kwargs.items():
            data[key] = value
        # Delete keys that we wish to ignore
        for ignore in ignored:
            if ignore in data:
                del data[ignore]
        # If the data already exists, we should update it instead of creating
        existing = cls.get_existing(data)
        if existing:
            existing.edit(data, update_version=False)
        else:
            existing = cls(**data)
            db.session.add(existing)
            db.session.commit()
        return existing

    @classmethod
    def get_existing(cls, data: dict) -> 'Optional[Base]':
        """
        Retrieve the existing object from the database (based on its `url` field)
        if it exists (else None).
        :param data: A dictionary representing a database object.
        :return: The object, or None if it does not exist.
        """
        if 'url' in data and data['url']:
            return cls.by_url(data['url'])

    @classmethod
    def by_id(cls, pk_id: Optional[int]) -> 'Optional[Base]':
        """
        Retrieve the object from the database by its `id`. If `None` is passed in, then
        `None` will be returned.
        :param pk_id:
        :return:
        """
        if pk_id is None:
            return None
        return cls.query.get(pk_id)

    def edit(self, updates: dict, update_version: bool = True) -> bool:
        """
        Modify this instance's fields based on the given keys and values of `updates`.
        Automatically commits the changes. By default, also updates the version number
        by one whenever this is called (but only if actual changes occur).
        :param updates:
        :param update_version:
        :return: Whether or not the object was modified.
        """
        modified = False
        for key, value in updates.items():
            if getattr(self, key) != value:
                modified = True
                setattr(self, key, value)
        if modified:
            if update_version:
                self.version += 1
            db.session.commit()
        return modified

    def encode_human(self):
        """ Create a human-friendly version of this data """
        return {'{id}.md'.format(id=self.id): json.dumps(self.encode_human())}
