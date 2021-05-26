"""Enum classes for Pysiaalarm."""
from enum import Enum, auto
from typing import Any


class AutoName(Enum):
    """Auto name the enums."""

    @staticmethod
    def _generate_next_value_(
        name: str, start: Any, count: Any, last_values: Any
    ) -> str:
        """Return name as value for Enum."""
        return name


class CommunicationsProtocol(AutoName):
    """CommunicationsProtocol enumerator for SIA."""

    TCP = auto()
    UDP = auto()


class ResponseType(AutoName):
    """Class with response types for events."""

    ACK = auto()
    DUH = auto()
    NAK = auto()
    RSP = auto()


class MessageTypes(Enum):
    """Message type enumerator for SIA."""

    SIADCS = "SIA-DCS"
    ADMCID = "ADM-CID"
    NULL = "NULL"
    OH = "OH"
