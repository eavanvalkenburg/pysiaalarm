# -*- coding: utf-8 -*-
"""Init for pysiaalarm."""
__author__ = "E.A. van Valkenburg"
__copyright__ = "E.A. van Valkenburg"
__license__ = "mit"

import sys

if sys.version_info[:2] >= (3, 8):
    # TODO: Import directly (no need for conditional) when `python_requires = >= 3.8`
    from importlib.metadata import PackageNotFoundError, version  # pragma: no cover
else:
    from importlib_metadata import PackageNotFoundError, version  # pragma: no cover

try:
    # Change here if project is renamed and does not equal the package name
    dist_name = __name__
    __version__ = version(dist_name)
except PackageNotFoundError:  # pragma: no cover
    __version__ = "unknown"
finally:
    del version, PackageNotFoundError

from .sia_account import SIAAccount, SIAResponseType
from .sia_client import SIAClient
from .sia_errors import (
    InvalidAccountFormatError,
    InvalidAccountLengthError,
    InvalidKeyFormatError,
    InvalidKeyLengthError,
)
from .sia_event import SIAEvent
from .sia_server import SIAServer
from .sia_const import Protocol
