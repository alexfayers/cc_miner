"""The main control page."""
import flask
from flask import Blueprint, render_template

app = flask.current_app
main = Blueprint("main", __name__)


@main.route("/")
def index() -> str:
    """Render the main control page."""
    return render_template("index.html")
