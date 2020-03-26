from flask import Flask, request
app = Flask(__name__)

@app_route('/')
def index():
    return "<h1>hello world!</h1>"

if __name__ == '__main__':
    app.run
