"""Class for SIA Accounts."""
import logging
from base64 import b64decode, b64encode
from binascii import hexlify, unhexlify
from datetime import datetime
from enum import Enum
from typing import Tuple

from Crypto import Random
from Crypto.Cipher import AES

from . import __author__, __copyright__, __license__, __version__
from .sia_errors import (
    InvalidAccountFormatError,
    InvalidAccountLengthError,
    InvalidKeyFormatError,
    InvalidKeyLengthError,
)
from .sia_event import SIAEvent

_LOGGER = logging.getLogger(__name__)


class SIAResponseType(Enum):
    """Class with response types for events."""

    ACK = 1
    DUH = 2
    NAK = 3


def _create_padded_message(message: str) -> str:
    """Create padded message, used for encrypted responses."""
    fill_size = len(message) + 16 - len(message) % 16
    return message.zfill(fill_size)


def _get_timestamp() -> str:
    """Create a timestamp in the right format."""
    return datetime.utcnow().strftime("_%H:%M:%S,%m-%d-%Y")


class SIAAccount:
    """Class for SIA Accounts."""

    def __init__(
        self,
        account_id: str,
        key: str = None,
        allowed_timeband: Tuple[int, int] = (40, 20),
    ):
        """Create a SIA Account.

        Arguments:
            account_id {str} -- The account id specified by the alarm system, should be 3-16 characters hexadecimal.

        Keyword Arguments:
            key {str} -- The encryption key specified by the alarm system, should be 16,24 or 32 characters hexadecimal. (default: {None})
            allowed_timeband {Tuple[int, int]} -- Seconds before and after current time that a message is valid in, unencrypted messages do not have to have a timestamp.

        """
        SIAAccount.validate_account(account_id, key)
        self.account_id = account_id
        self.key = key.encode("utf-8") if key else key
        self.allowed_timeband = allowed_timeband
        self.encrypted = False
        self._create_crypters()

    def _create_crypters(self):
        """Create the de- and encrypter functions."""
        if self.key:
            self.decrypter = AES.new(
                self.key, AES.MODE_CBC, unhexlify("00000000000000000000000000000000")
            )
            self.encrypter = AES.new(
                self.key, AES.MODE_CBC, unhexlify("00000000000000000000000000000000")
            )
            self.encrypted = True
        else:
            self.decrypter = None
            self.encrypter = None

    def encrypt(self, message: str) -> str:
        """Encrypt a string, usually used for endings.

        Arguments:
            message {str} -- String to encrypt.

        Returns:
            str -- Encrypted string, if encrypted account.

        """
        if self.encrypted:
            message = _create_padded_message(message)
            encrypted_message = hexlify(self.encrypter.encrypt(message.encode("utf-8")))
            return encrypted_message.decode(encoding="utf-8").upper()

        else:
            return message

    def decrypt(self, event: SIAEvent) -> SIAEvent:
        """Decrypt the event, if the account is encrypted, otherwise pass back the event.

        Arguments:
            event {SIAEvent} -- Event to be decrypted.

        Returns:
            SIAEvent -- Event decrypted, with parsed fields.

        """
        if self.encrypted and event.encrypted_content:
            decrypted_content = self.decrypter.decrypt(
                unhexlify(event.encrypted_content)
            )
            event.content = decrypted_content.decode("utf-8", errors="backslashreplace")
        return event

    def create_response(self, event: SIAEvent, response_type: SIAResponseType) -> str:
        """Create a response message, based on account, event and response type.

        Arguments:
            event {SIAEvent} -- Event to respond to.
            response_type {SIAResponseType} -- Response type.

        Returns:
            str -- Response to send back to sender.

        """
        if response_type == SIAResponseType.ACK and event:
            if self.encrypted:
                res = f'"*ACK"{event.sequence}L0#{event.account}[{self.encrypt(_create_padded_message("]")+_get_timestamp())}'
            else:
                res = f'"ACK"{event.sequence}L0#{event.account}[]'
        elif response_type == SIAResponseType.DUH and event:
            res = f'"DUH"{event.sequence}L0#{event.account}[]'
        elif response_type == SIAResponseType.NAK:
            res = f'"NAK"0000L0R0A0[]{_get_timestamp()}'
        elif not response_type:
            return b"\n\r"
        else:
            _LOGGER.warning(
                "Could not find the right response message for response type: %s and optional event: %s",
                response_type,
                event,
            )
            return b"\n\r"

        header = ("%04x" % len(res)).upper()
        return f"\n{SIAEvent.crc_calc(res)}{header}{res}\r".encode("utf-8")

    @classmethod
    def validate_account(cls, account_id: str = None, key: str = None):
        """Validate a accounts information, can be used before creating as well. Can be used to check the individual arguments as well.

        Keyword Arguments:
            account_id {str} -- The account id specified by the alarm system, should be 3-16 characters hexadecimal. (default: {None})
            key {str} -- The encryption key specified by the alarm system, should be 16,24 or 32 characters hexadecimal. (default: {None})

        Raises:
            InvalidKeyFormatError: If the key is not a valid hexadecimal string.
            InvalidKeyLengthError: If the key does not have 16, 24 or 32 characters.
            InvalidAccountFormatError: If the account id is not a valid hexadecimal string.
            InvalidAccountLengthError: If the account id does not have between 3 and 16 characters.

        Returns:
            bool, error -- Returns True if all was good, an error is raised otherwise.

        """
        if key:
            try:
                int(key, 16)
            except ValueError:
                raise InvalidKeyFormatError
            try:
                assert len(key) in (16, 24, 32)
            except AssertionError:
                raise InvalidKeyLengthError
        if account_id:
            try:
                int(account_id, 16)
            except ValueError:
                raise InvalidAccountFormatError
            try:
                assert 3 <= len(account_id) <= 16
            except AssertionError:
                raise InvalidAccountLengthError

        return True
