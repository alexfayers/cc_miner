"""The main functionality of `cc_miner`."""

import logging

from ._helper import Config
from .web.app import create_app


class BaseClass:
    """Everything in the project comes back to here."""

    def __init__(self, config_file: str):
        """Initialises the base class for `cc_miner` by loading the config and setting up a logger.

        Args:
            config_file (str): Path to a config file containing settings for the class.
        """
        self.logger = logging.getLogger(__name__).getChild(self.__class__.__qualname__)

        self.config = Config(config_file)

        package_logger = logging.getLogger("cc_miner")
        if self.config.DEBUG.ENABLED:
            package_logger.setLevel(logging.DEBUG)
        else:
            package_logger.setLevel(logging.INFO)

    def start_server(self) -> None:
        """Start the webserver in development mode."""
        app = create_app()
        app.run("0.0.0.0", 5000, debug=True)
