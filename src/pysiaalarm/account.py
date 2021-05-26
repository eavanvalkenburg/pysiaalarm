"""Class for SIA Accounts."""
import logging
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config, Exclude
from typing import Optional, Tuple

from .errors import (
    InvalidAccountFormatError,
    InvalidAccountLengthError,
    InvalidKeyFormatError,
    InvalidKeyLengthError,
)

_LOGGER = logging.getLogger(__name__)


@dataclass_json
@dataclass
class SIAAccount:
    """Class for SIA Accounts."""

    account_id: str
    key: Optional[str] = None
    allowed_timeband: Tuple[int, int] = (40, 20)
    key_b: Optional[bytes] = field(
        repr=False, default=None, metadata=config(exclude=Exclude.ALWAYS)  # type: ignore
    )

    def __post_init__(self) -> None:
        """Rewrite the key as bytes."""
        self.key_b = self.key.encode("utf-8") if self.key else None

    @property
    def encrypted(self) -> bool:
        """Return true when encrypted."""
        return True if self.key_b else False

    @classmethod
    def validate_account(cls, account_id: str = None, key: str = None) -> None:
        """Validate a accounts information, can be used before creating as well. Can be used to check the individual arguments as well.

        Keyword Arguments:
            account_id {str} -- The account id specified by the alarm system, should be 3-16 characters hexadecimal. (default: {None})
            key {str} -- The encryption key specified by the alarm system, should be 16,24 or 32 characters hexadecimal. (default: {None})

        Raises:
            InvalidKeyFormatError: If the key is not a valid hexadecimal string.
            InvalidKeyLengthError: If the key does not have 16, 24 or 32 characters.
            InvalidAccountFormatError: If the account id is not a valid hexadecimal string.
            InvalidAccountLengthError: If the account id does not have between 3 and 16 characters.

        """
        if account_id is not None:  # pragma: no cover
            try:
                int(account_id, 16)
            except ValueError:
                raise InvalidAccountFormatError
            try:
                assert 3 <= len(account_id) <= 16
            except AssertionError:
                raise InvalidAccountLengthError
        if key is not None:  # pragma: no cover
            try:
                int(key, 16)
            except ValueError:
                raise InvalidKeyFormatError
            try:
                assert len(key) in (16, 24, 32)
            except AssertionError:
                raise InvalidKeyLengthError
