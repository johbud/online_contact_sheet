from collections import Iterable
from config import Config
from werkzeug.datastructures import FileStorage
from flask_wtf.file import FileAllowed
from wtforms.validators import StopValidation

class UploadValidator(object):

    def __init__(self, allowed_filetypes, message=None):
        self.allowed_filetypes = allowed_filetypes
        self.message = message

    def __call__(self, form, field):
        if not (all(isinstance(item, FileStorage) for item in field.data) and field.data):
            raise StopValidation(self.message or field.gettext("Invalid file."))

        for data in field.data:
            filename = data.filename.lower()

            if isinstance(self.allowed_filetypes, Iterable):
                if any(filename.endswith("." + x) for x in self.allowed_filetypes):
                    self.check_size(data, field)
                    return

                raise StopValidation(self.message or field.gettext(
                    "File does not have an approved extension: {extensions}"
                ).format(extensions=", ".join(self.allowed_filetypes)))

            if not self.allowed_filetypes.file_allowed(field.data, filename):
                raise StopValidation(self.message or field.gettext(
                    "File does not have an approved extension."
                ))

    def check_size(self, file, field):
            file.seek(0,2)
            if file.tell() < Config.FILE_SIZE_LIMIT:
                file.seek(0)
                return

            raise StopValidation(self.message or field.gettext("File exceeds file size limit."))
