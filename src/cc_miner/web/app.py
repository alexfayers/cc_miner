"""App initialisation."""
from typing import Optional

from flask import Flask

from .routes import main


def create_app(config_filename: Optional[str] = None) -> Flask:
    """Create and return a flask app.

    Args:
        config_filename (Optional[str]): Path to a config file containing settings for the class.

    Returns:
        Flask: Flask app.
    """
    app = Flask(__name__)
    if config_filename is not None:
        app.config.from_pyfile(config_filename)

    app.register_blueprint(main.main)
    return app


app = create_app()
