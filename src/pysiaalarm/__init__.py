# -*- coding: utf-8 -*-
__author__ = "E.A. van Valkenburg"
__copyright__ = "E.A. van Valkenburg"
__license__ = "mit"

from pkg_resources import DistributionNotFound, get_distribution

try:
    dist_name = __name__
    __version__ = get_distribution(dist_name).version
except DistributionNotFound:
    __version__ = "unknown"
finally:
    del get_distribution, DistributionNotFound

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
