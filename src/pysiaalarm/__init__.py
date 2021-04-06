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
    from importlib_metadata import (  # pylint: disable=F0401; pragma: no cover
        PackageNotFoundError,
        version,
    )

try:
    # Change here if project is renamed and does not equal the package name
    dist_name = __name__
    __version__ = version(dist_name)
except PackageNotFoundError:  # pragma: no cover
    __version__ = "unknown"
finally:
    del version, PackageNotFoundError

from .account import SIAAccount
from .sync.client import SIAClient
from .errors import (
    InvalidAccountFormatError,
    InvalidAccountLengthError,
    InvalidKeyFormatError,
    InvalidKeyLengthError,
)
from .event import SIAEvent, OHEvent
from .utils import CommunicationsProtocol
