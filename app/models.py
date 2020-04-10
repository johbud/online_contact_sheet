from app import db, login
from uuid import uuid4
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    passwordhash = db.Column(db.String(128))
    sheets = db.relationship("Sheet", backref="user", lazy="dynamic")
    images = db.relationship("Image", backref="user", lazy="dynamic")

    def set_password(self, password):
        self.passwordhash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.passwordhash, password)

    def __repr__(self):
        return "<User {}>".format(self.username)

class Sheet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36))
    name = db.Column(db.String(128))
    description = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    images = db.relationship("Image", backref="sheet", lazy="dynamic")

    def set_uuid(self):
        self.uuid = str(uuid4())

    def __repr__(self):
        return "<Sheet {}>".format(self.name)

class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    path = db.Column(db.Text)
    comment = db.Column(db.Text)
    rating = db.Column(db.SmallInteger)
    sheet_id = db.Column(db.Integer, db.ForeignKey("sheet.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    def __repr__(self):
        return "<Image {}>".format(self.name)
