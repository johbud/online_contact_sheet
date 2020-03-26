from flask import Flask, request
app = Flask(__name__)

@app_route('/', methods=["GET"])
def index():
    return "<h1>hello world!</h1>"
