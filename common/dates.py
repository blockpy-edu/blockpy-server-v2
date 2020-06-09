"""
Common utility functions for managing dates and times.
"""

from datetime import datetime


def datetime_to_string(a_datetime: datetime) -> str:
    """
    Convert the given datetime to a string representation
    :param a_datetime: A datetime object
    :return: The string representation
    """
    return a_datetime.isoformat() + 'Z'


def string_to_datetime(a_string: str) -> datetime:
    """
    Convert the given string to a datetime. Initially tries the string with a decimal
    place, then tries it without. Strings should be roughly of the format:

    > '%Y-%m-%dT%H:%M:%S.%fZ'

    :param a_string: A string representation of a datetime.
    :return: The datetime version of that string
    """
    try:
        return datetime.strptime(a_string, '%Y-%m-%dT%H:%M:%S.%fZ')
    except ValueError:
        return datetime.strptime(a_string, '%Y-%m-%dT%H:%M:%SZ')


def datetime_to_pretty_string(a_datetime: datetime) -> str:
    """
    Creates a string representation of the datetime that is easier to read for humans.
    :param a_datetime: Datetime object.
    :return: String representation of the datetime.
    """
    return a_datetime.strftime("%I:%M%p on %a %d, %b %Y").replace(" 0", " ")
