import os
import threading
from uuid import uuid4

from botocore.exceptions import ClientError
from flask import flash, redirect, render_template, request, url_for, session
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename

from app import app, db, s3, redis_db
from app.forms import LoginForm, NewContactsheetForm, RegisterForm
from app.generate_pdf import generate_pdf
from app.models import Image, Sheet, User
from app.size_of import size_of
from config import Config


class Upload_thread(threading.Thread):
    def __init__(self, form, user_id, thread_id):
        self.progress = 0
        self.chunks = 0
        self.percentage = 0
        self.form = form
        self.user_id = user_id
        self.thread_id = thread_id
        super().__init__()

    def update_progress(self, error=None):
        if error:
            redis_db.set(self.thread_id, error)
        else:
            self.progress += 1
            self.percentage = self.progress/self.chunks * 100
            redis_db.set(self.thread_id, self.percentage)

    def run(self):
        if self.form.generate_pdf.data:
            self.chunks = len(self.form.files.data) * 2 + 1
        else:
            self.chunks = len(self.form.files.data)

        sheet = Sheet(name=self.form.name.data, user_id=self.user_id, pdf=self.form.generate_pdf.data, show_name=self.form.show_name.data)
        sheet.set_uuid()
        db.session.add(sheet)
        db.session.flush()

        images = []

        for file in self.form.files.data:
            file_url = str(sheet.uuid) + "/" + secure_filename(file.filename)
            if self.form.hide_extension.data:
                name = os.path.splitext(file.filename)[0]
            else:
                name = file.filename
            
            try:
                s3.upload_fileobj(file.stream, Config.S3_BUCKET, file_url, ExtraArgs={'ACL': 'public-read'})
            except ClientError as e:
                self.update_progress(error=e)
                return
            images.append(Image(name=name, path=file_url, sheet_id=sheet.id, user_id=self.user_id))
            self.update_progress()

        for image in images:
            db.session.add(image)

        if self.form.generate_pdf.data:
            try:
                pdf = generate_pdf(images=images, sheet_name=sheet.name, url_root=Config.S3_URL, orientation=self.form.pdf_orientation.data, progress=self, show_name=self.form.show_name.data)
                pdf_url = str(sheet.uuid) + "/" + pdf
            except:
                self.update_progress(error="Could not generate pdf.")
                return
            
            try:
                s3.upload_file(pdf, Config.S3_BUCKET, pdf_url, ExtraArgs={'ACL': 'public-read'})
                os.remove(pdf)
            except ClientError as e:
                self.update_progress(error=e)
                return
            self.update_progress()

        db.session.commit()

        
