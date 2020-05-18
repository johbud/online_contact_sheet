import redis
from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bootstrap import Bootstrap
import boto3

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = "login"
bootstrap = Bootstrap(app)
s3 = boto3.client("s3", region_name=Config.AWS_REGION, aws_access_key_id=Config.AWS_ACCESS_KEY, aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY)
if Config.REDIS_URL:
    redis_db = redis.from_url(Config.REDIS_URL)
else:
    redis_db = redis.Redis()

from app import routes, models
