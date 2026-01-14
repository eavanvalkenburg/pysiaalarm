"""Class for SIA Accounts."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field, asdict
from typing import Any
from datetime import tzinfo
import pytz

from .errors import (
    InvalidAccountFormatError,
    InvalidAccountLengthError,
    InvalidKeyFormatError,
    InvalidKeyLengthError,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class SIAAccount:
    """Class for SIA Accounts."""

    account_id: str = ""
    key: str | None = None
    allowed_timeband: tuple[int, int] | None = (40, 20)
    device_timezone: tzinfo = pytz.utc
    response_qualifier: str = ""
    key_b: bytes | None = field(
        repr=False,
        default=None,  # metadata=config(exclude=Exclude.ALWAYS)  # type: ignore
    )

    def __post_init__(self) -> None:
        """Rewrite the key as bytes."""
        self.key_b = self.key.encode("utf-8") if self.key else None
        self.account_id = self.account_id.upper()
        self.response_qualifier = self.response_qualifier.upper()

    @property
    def encrypted(self) -> bool:
        """Return true when encrypted."""
        return bool(self.key_b)

    @classmethod
    def validate_account(
        cls, account_id: str | None = None, key: str | None = None
    ) -> None:
        """Validate a accounts information, either with one of the fields or both.

        Keyword Arguments:
            account_id {str} -- The account id specified by the alarm system,
                should be 3-16 characters hexadecimal. (default: {None})
            key {str} -- The encryption key specified by the alarm system,
                should be 16,24 or 32 characters hexadecimal. (default: {None})

        Raises:
            InvalidKeyFormatError: If the key is not a valid hexadecimal string.
            InvalidKeyLengthError: If the key does not have 16, 24 or 32 characters.
            InvalidAccountFormatError: If the account id is not a valid hexadecimal string.
            InvalidAccountLengthError: If the account id does not have between 3 and 16 characters.

        """
        if account_id:  # pragma: no cover
            try:
                int(account_id, 16)
            except ValueError as exc:
                raise InvalidAccountFormatError from exc
            try:
                assert 3 <= len(account_id) <= 16
            except AssertionError as exc:
                raise InvalidAccountLengthError from exc
        if key is not None:  # pragma: no cover
            try:
                int(key, 16)
            except ValueError as exc:
                raise InvalidKeyFormatError from exc
            try:
                assert len(key) in (16, 24, 32)
            except AssertionError as exc:
                raise InvalidKeyLengthError from exc

    def to_dict(self) -> dict[str, Any]:
        """Create a dict from the dataclass."""
        return asdict(self)

    @classmethod
    def from_dict(cls, acc: dict[str, Any]) -> SIAAccount:
        """Create a SIA Account from a dict."""
        return cls(**acc)
