"""Init for pysiaalarm."""
__author__ = "E.A. van Valkenburg"
__copyright__ = "E.A. van Valkenburg"
__license__ = "mit"

import sys
from importlib.metadata import PackageNotFoundError, version

try:
    # Change here if project is renamed and does not equal the package name
    dist_name = __name__
    __version__ = version(dist_name)
except PackageNotFoundError:  # pragma: no cover
    __version__ = "unknown"
finally:
    del version, PackageNotFoundError

from .account import SIAAccount
from .errors import (
    InvalidAccountFormatError,
    InvalidAccountLengthError,
    InvalidKeyFormatError,
    InvalidKeyLengthError,
)
from .event import OHEvent, SIAEvent
from .sync.client import SIAClient
from .utils import CommunicationsProtocol
