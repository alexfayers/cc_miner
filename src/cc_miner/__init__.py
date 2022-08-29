""".. include:: ../../README.md"""  # noqa

import logging

from . import core
from ._helper import ColoredFormatter as _ColoredFormatter
from ._helper import SuccessLogger as _SuccessLogger

__all__ = ["core", "web"]

# set up logging for the package
logging.setLoggerClass(_SuccessLogger)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
console = logging.StreamHandler()
console.setFormatter(_ColoredFormatter("[%(name)s] (%(levelname)s): %(message)s"))
logger.addHandler(console)
