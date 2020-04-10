import os
from app import app, db, s3
from config import Config
from uuid import uuid4
from flask import render_template, redirect, request, url_for, flash
from app.forms import LoginForm, RegisterForm, NewContactsheetForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Sheet, Image
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
from botocore.exceptions import ClientError


@app.route("/")
@app.route("/index")
@login_required
def index():
    sheets = Sheet.query.filter_by(user_id=current_user.get_id()).all()
    url_root = request.url_root

    return render_template("index.html", sheets=sheets, url_root=url_root)

@app.route("/login", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:
        return redirect(url_for("index"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash("Invalid username or password")
            return redirect(url_for("login"))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get("next")
        if not next_page or url_parse(next_page).netloc != "":
            next_page = url_for("index")

        return redirect(next_page)
    return render_template("login.html", form = form)

@app.route("/register", methods=["GET", "POST"])
def register():

    if current_user.is_authenticated:
        return redirect(url_for("index"))

    form = RegisterForm()
    if form.validate_on_submit():
        if Config.PRIVATE:
            if form.private_key.data != Config.PRIVATE_REGISTRATION_KEY:
                flash("Invalid invite key.")
                return render_template("register.html", form=form)
        user = User(username=form.username.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        flash("You are now registered.")
        return redirect(url_for("login"))

    return render_template("register.html", form=form)


@app.route("/create", methods=["GET", "POST"])
@login_required
def create_contactsheet():

    form = NewContactsheetForm()

    if form.validate_on_submit():
        sheet = Sheet(name=form.name.data, user_id=current_user.get_id())
        sheet.set_uuid()
        db.session.add(sheet)
        db.session.flush()

        images = []

        for file in form.files.data:
            file_url = str(sheet.uuid) + "/" + secure_filename(file.filename)
            if form.hide_extension.data:
                name = os.path.splitext(file.filename)[0]
            else:
                name = file.filename

            try:
                s3.upload_fileobj(file.stream, Config.S3_BUCKET, file_url, ExtraArgs={'ACL': 'public-read'})
            except ClientError as e:
                flash(e)
                return redirect(url_for("create_contactsheet"))
            images.append(Image(name=name, path=file_url, sheet_id=sheet.id, user_id=current_user.get_id()))

        for image in images:
            db.session.add(image)

        db.session.commit()
        flash("Successfully created contact sheet")

        return redirect(url_for("index"))

    return render_template("/create.html", form=form)

@app.route("/delete", methods=["GET", "POST"])
@login_required
def delete():

    if request.method == "POST":
        uuid = request.form.get("sheet_uuid")
        sheet = Sheet.query.filter_by(uuid=uuid).first()
        if not sheet:
            flash("Sheet not found. " + uuid)
            return redirect(url_for("index"))

        images = Image.query.filter_by(sheet_id=sheet.id).all()

        if int(sheet.user_id) != int(current_user.get_id()):
            flash("You do not have permission to delete this sheet.")
            return redirect(url_for("index"))

        for image in images:
            try:
                s3.delete_object(Bucket=Config.S3_BUCKET, Key=image.path)
            except ClientError as e:
                flash("Error while deleting files: " + e)
                return redirect(url_for("index"))

        try:
            Image.query.filter_by(sheet_id=sheet.id).delete()
            Sheet.query.filter_by(uuid=uuid).delete()
            db.session.commit()
        except:
            flash("Database error while deleting sheet.")
            return redirect(url_for("index"))

        flash("Successfully deleted " + sheet.name)

    return redirect(url_for("index"))

@app.route("/sheet/<sheet_id>")
def sheet_view(sheet_id):

    sheet = Sheet.query.filter_by(uuid=sheet_id).first()
    images = Image.query.filter_by(sheet_id=sheet.id).all()

    if not images:
        return render_template("404.html")

    s3_url_root = Config.S3_URL
    app_url_root = request.url_root

    return render_template("contactsheet_main.html", images=images, sheet=sheet, s3_url_root=s3_url_root, app_url_root=app_url_root, active_index=1)

@app.route("/sheet/<sheet_id>/<selected_index>")
def sheet_view_selected(sheet_id, selected_index):

    sheet = Sheet.query.filter_by(uuid=sheet_id).first()
    images = Image.query.filter_by(sheet_id=sheet.id).all()

    if not images:
        return render_template("404.html")

    s3_url_root = Config.S3_URL
    app_url_root = request.url_root

    active_index = int(selected_index)

    return render_template("contactsheet_main.html", images=images, sheet=sheet, s3_url_root=s3_url_root, app_url_root=app_url_root, active_index=active_index)


@app.route("/sheet/overview/<sheet_id>")
def sheet_overview(sheet_id):

    sheet = Sheet.query.filter_by(uuid=sheet_id).first()
    images = Image.query.filter_by(sheet_id=sheet.id).all()

    if not images or not sheet:
        return render_template("404.html")

    s3_url_root = Config.S3_URL
    app_url_root = request.url_root

    return render_template("contactsheet_overview.html", images=images, sheet=sheet, s3_url_root=s3_url_root, app_url_root=app_url_root)

@app.route("/logout")
def logout():
    logout_user()
    return redirect("index")
