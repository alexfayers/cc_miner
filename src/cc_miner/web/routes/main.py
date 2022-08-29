"""The main control page."""
import flask
from flask import render_template, Blueprint

app = flask.current_app
main = Blueprint('main', __name__)


@main.route('/')
def index() -> str:
    """Render the main control page."""
    return render_template('index.html')
