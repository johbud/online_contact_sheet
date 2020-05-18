import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'this_is_secret'
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or "sqlite:///" + os.path.join(basedir, "app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    AWS_ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY")
    AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
    AWS_REGION = os.environ.get("AWS_REGION")
    S3_BUCKET = os.environ.get("S3_BUCKET")
    S3_URL = os.environ.get("S3_URL")
    PRIVATE = True
    PRIVATE_REGISTRATION_KEY = os.environ.get("PRIVATE_REGISTRATION_KEY")
    FILE_SIZE_LIMIT = os.environ.get("FILE_SIZE_LIMIT") or 2 * 1024 * 1024
    REDIS_URL = os.environ.get("REDIS_URL") or None