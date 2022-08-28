"""CLI functionality of `cc_miner`."""

import logging
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser

from . import BaseClass


def cli_main() -> None:
    """CLI entrypoint for `cc_miner`. Uses `BaseClass`."""
    argparser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    argparser.add_argument(
        "-c", "--config", help="Path to config file", type=str, default="config.yml"
    )
    argparser.add_argument(
        "-v", "--verbose", help="Enable verbose logging", action="store_true"
    )

    args = argparser.parse_args()
    config_file = args.config
    verbose_logging = args.verbose

    if verbose_logging:
        logger = logging.getLogger("cc_miner")
        logger.setLevel(logging.DEBUG)

    app = BaseClass(config_file)

    app.logger.info(
        f"Hi, welcome to {app.config.INFO.NAME} by {app.config.INFO.AUTHOR}!"
    )

    app.logger.debug("We're in debug mode!")
