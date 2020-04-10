from app import app, db
from app.models import User, Sheet, Image

@app.shell_context_processor
def make_shell_context():
    return {"db": db, "User" : User, "Sheet" : Sheet, "Image": Image}
