"""
Very simple implementation of a Tribes keyserver server.
Right now, the keyserver will do the following:
1) check for username collisions
2) add public keys
3) retrieve public keys by username

"""

from flask import Flask

app = Flask(__name__)

@app.route("/")
def index():
  return "ok.computer"
