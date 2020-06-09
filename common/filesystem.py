"""
Helper functions for managing the filesystem
"""
import os


def ensure_dirs(path: str):
    """
    Ensure that the directory exists, or log an error if it doesn't.
    :param path: The path to the directory.
    :return:
    """
    try:
        os.makedirs(path)
    except OSError:
        if not os.path.isdir(path):
            pass
            # TODO: What should now happen instead?
            # app.logger.warning(e.args + (path,))
