from app import db

class User(db.model):
    id = db.Column(db.Integer, primary_key=true)
    username = db.Column(db.String(64), index=True, unique=True)
    passwordhash = db.Column(db.String(128))

    def __repr__(self):
        return "<User {}>".format(self.username)
