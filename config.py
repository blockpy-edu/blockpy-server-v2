"""
Flask Configuration File
"""
import os


class DefaultConfig:
    """
    General settings for all configurations
    """
    SITE_NAME = 'BlockPy Public'
    SHOW_ABOUT_PAGE = True
    SITE_VERSION = 6
    DEBUG = True
    TESTING = True
    CSRF_ENABLED = True
    WTF_CSRF_ENABLED = True
    SYS_ADMINS = ['Unknown']
    ROOT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
    STATIC_DIRECTORY = os.path.join(ROOT_DIRECTORY, 'static')
    UPLOADS_DIR = os.path.join(STATIC_DIRECTORY, 'uploads')
    BLOCKPY_LOG_DIR = os.path.join(ROOT_DIRECTORY, 'logs')
    ERROR_FILE_PATH = os.path.join(ROOT_DIRECTORY, 'logs', 'blockpy_errors.log')
    EVENTS_FILE_PATH = os.path.join(ROOT_DIRECTORY, 'logs', 'blockpy_events.log')
    BLOCKPY_SOURCE_DIR = None
    CORGIS_URL = "https://corgis-edu.github.io/corgis/datasets/"
    # Maximum student code size (Defaults to 500kb)
    MAXIMUM_CODE_SIZE = 500 * 1024

    # Session settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'None'
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = True
    COOKIE_SAMESITE = 'None'

    # Outgoing mail server: configured for GMAIL by default
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    SECURITY_EMAIL_SENDER = "BlockPy Administrator"

    # Debug toolbar settings
    DEBUG_TB_INTERCEPT_REDIRECTS = False

    # Flask JWT Extended
    JWT_TOKEN_LOCATION = ["headers", "cookies", "json", "query_string"]
    JWT_COOKIE_SAMESITE = 'None'
    JWT_COOKIE_SECURE = True

    # User registration stuff
    SECURITY_CONFIRMABLE = True
    SECURITY_REGISTERABLE = True
    SECURITY_RECOVERABLE = True
    SECURITY_CHANGEABLE = True
    SECURITY_URL_PREFIX = '/users'
    SECURITY_POST_LOGIN_VIEW = "/blockpy"
    SECURITY_PASSWORD_HASH = 'bcrypt'
    SECURITY_DEFAULT_REMEMBER_ME = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class ProductionConfig(DefaultConfig):
    """
    General settings for production mode
    """
    DEBUG = False


class DevelopmentConfig(DefaultConfig):
    """
    General settings for local development
    """
    DEBUG = True
    HOST = 'localhost'
    SITE_ROOT_URL = 'localhost:5001'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///instance/main.db'


class TestConfig(DefaultConfig):
    """ Simple test config with in-memory database """
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://:memory:'
