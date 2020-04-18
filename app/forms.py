from flask_wtf import FlaskForm
from flask_wtf.file import FileRequired, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, RadioField, SubmitField, FileField, MultipleFileField, TextAreaField
from wtforms.validators import DataRequired, EqualTo, ValidationError
from app.models import User
from config import Config
from app.upload_validator import UploadValidator

class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember me")
    submit = SubmitField("Sign in")

class RegisterForm(FlaskForm):
    if Config.PRIVATE:
        private_key = StringField("Invite key", validators=[DataRequired()])
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    password_confirm = PasswordField("Confirm password", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Register")

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError("Please choose another username")

class NewContactsheetForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    files = MultipleFileField("Images", validators=[UploadValidator(["jpg", "png"])])
    hide_extension = BooleanField("Hide file extensions")
    generate_pdf = BooleanField("Generate PDF")
    pdf_orientation = RadioField("PDF Orientation", choices=[("L","Landscape"),("P","Portrait")], default="L")
    submit = SubmitField("Create")
