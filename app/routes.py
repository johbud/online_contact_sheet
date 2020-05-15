import os
import time
import random
import redis
from uuid import uuid4

from botocore.exceptions import ClientError
from flask import flash, redirect, render_template, request, url_for, Response, session
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename

from app import app, db, s3, redis_db
from app.forms import LoginForm, NewContactsheetForm, RegisterForm
from app.generate_pdf import generate_pdf
from app.models import Image, Sheet, User
from app.size_of import size_of
from app.upload_thread import Upload_thread
from config import Config


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

@app.route("/progress/<int:thread_id>")
def progress(thread_id):
    def progress_generator(thread_id):
        while int(float(redis_db.get(thread_id).decode("utf-8"))) < 100:
            yield "data:" + redis_db.get(thread_id).decode("utf-8") + "\n\n"
    return Response(progress_generator(thread_id), mimetype="text/event-stream")
  
@app.route("/create", methods=["GET", "POST"])
@login_required
def create_contactsheet():

    form = NewContactsheetForm()
    thread_id = current_user.get_id()

    redis_db.set(thread_id, "0")
    if form.validate_on_submit():
        upload_thread = Upload_thread(form, current_user.get_id(), thread_id)
        upload_thread.start()

        while int(float(redis_db.get(thread_id).decode("utf-8"))) < 100:
            print(redis_db.get(thread_id).decode("utf-8"))
            time.sleep(0.1)
        flash("Successfully created contact sheet")
        return redirect(url_for("index"))

    return render_template("/create.html", form=form, max_file_size=size_of(Config.FILE_SIZE_LIMIT), thread_id=thread_id)

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
        
        if sheet.pdf:
            pdf_path = sheet.uuid + "/" + secure_filename(sheet.name) + ".pdf"
            try:
                s3.delete_object(Bucket=Config.S3_BUCKET, Key=pdf_path)
            except ClientError as e:
                flash("Error while deleting pdf: " + e)
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
    
    if sheet.pdf:
        pdf_name = secure_filename(sheet.name) + ".pdf"
    else:
        pdf_name = None

    return render_template("contactsheet_main.html", images=images, sheet=sheet, s3_url_root=s3_url_root, app_url_root=app_url_root, active_index=1, pdf_name=pdf_name)

@app.route("/sheet/<sheet_id>/<selected_index>")
def sheet_view_selected(sheet_id, selected_index):

    sheet = Sheet.query.filter_by(uuid=sheet_id).first()
    images = Image.query.filter_by(sheet_id=sheet.id).all()

    if not images:
        return render_template("404.html")

    s3_url_root = Config.S3_URL
    app_url_root = request.url_root

    if sheet.pdf:
        pdf_name = secure_filename(sheet.name) + ".pdf"
    else:
        pdf_name = None

    active_index = int(selected_index)

    return render_template("contactsheet_main.html", images=images, sheet=sheet, s3_url_root=s3_url_root, app_url_root=app_url_root, active_index=active_index, pdf_name=pdf_name)


@app.route("/sheet/overview/<sheet_id>")
def sheet_overview(sheet_id):

    sheet = Sheet.query.filter_by(uuid=sheet_id).first()
    images = Image.query.filter_by(sheet_id=sheet.id).all()

    if not images or not sheet:
        return render_template("404.html")

    s3_url_root = Config.S3_URL
    app_url_root = request.url_root
    
    if sheet.pdf:
        pdf_name = secure_filename(sheet.name) + ".pdf"
    else:
        pdf_name = None

    return render_template("contactsheet_overview.html", images=images, sheet=sheet, s3_url_root=s3_url_root, app_url_root=app_url_root, pdf_name=pdf_name)

@app.route("/logout")
def logout():
    logout_user()
    return redirect("index")
