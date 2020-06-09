"""
Helper functions related to accessing and manipulating data stored in objects.
"""
from typing import Union, Any, Callable
from sqlalchemy import Table


def optional_encoded_field(id_value: int, owning_object: Union[bool, Table],
                           query: Callable, attr: str) -> Any:
    """
    Access data for a model, if it is given, using the given database information if
    available.

    'owner_id__email': optional_encoded_field(self.owner_id, use_owner, models.User.query.get, 'email'),

    :param id_value:
    :param owning_object:
    :param query:
    :param attr:
    :return:
    """
    if owning_object is not False:
        if owning_object is True:
            owning_object = query(id_value)
        if owning_object:
            return getattr(owning_object, attr)
    return ""
