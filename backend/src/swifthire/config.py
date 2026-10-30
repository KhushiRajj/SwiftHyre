import os


class BaseConfig:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///:memory:')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ONLINECOMPILER_API_KEY = os.environ.get('ONLINECOMPILER_API_KEY')


def get_config():
    return BaseConfig
