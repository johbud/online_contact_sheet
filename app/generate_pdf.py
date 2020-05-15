import os
from io import BytesIO

import requests
from fpdf import FPDF
from PIL import Image
from werkzeug.utils import secure_filename


def generate_pdf(images, sheet_name, url_root, orientation="P", progress=None):

    pdf = FPDF(orientation=orientation,unit="mm",format="A4")
    pdf.set_font("Helvetica", size=12)
    pdf.set_auto_page_break(False)

    for image in images:

        pdf.add_page()
        pdf.set_x(0)

        if orientation == "P":
            page_width = 210
            page_height = 297
        else:
            page_width = 297
            page_height = 210

        response = requests.get(url_root + image.path)
        filename = image.path.split("/", 1)[1]

        with Image.open(BytesIO(response.content)) as im:

            width, height = fit_image(im, page_width, page_height)
            x, y = center_image(page_width, page_height, width, height)
            im.save(filename, format=im.format)

            pdf.image(filename, x=x, y=y, w=width, h=height)

            # Clean-up
            os.remove(filename)

        pdf.set_xy((page_width - 180) / 2, page_height - 20)
        pdf.cell(180, 15, txt=image.name, align="C")
        if progress:
                progress.update_progress()

    pdf_name = secure_filename(sheet_name+".pdf")
    pdf.output(name=pdf_name)

    return pdf_name

def fit_image(image, page_width, page_height, x_margin=20, y_margin=20):
    max_width = page_width - (x_margin * 2)
    max_height = page_height - (y_margin * 2)

    if image.width < image.height:
        ratio = image.width / image.height
        height = max_height
        width = height * ratio
    else:
        ratio = image.height / image.width
        width = max_width
        height = width * ratio

    if width > max_width:
        width = max_width
        height = (max_width / width) * height
    if height > max_height:
        height = max_height
        width = (max_height / height) * width        

    return width, height

def center_image(page_width, page_height, width, height):
    x = (page_width - width) / 2
    y = (page_height - height) / 2

    return x, y
