from flask import Flask, request, abort
import os

app = Flask(__name__)


@app.route("/")
def test():
    return "Report bot!"


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='127.0.0.1', port=port)