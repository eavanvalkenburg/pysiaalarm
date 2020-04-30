"""Class for SIA Accounts."""

from binascii import hexlify, unhexlify
import logging
from Crypto import Random
from Crypto.Cipher import AES

from pysiaalarm import __version__
from pysiaalarm.sia_event import SIAEvent
from pysiaalarm.sia_errors import (
    InvalidAccountFormatError,
    InvalidAccountLengthError,
    InvalidKeyFormatError,
    InvalidKeyLengthError,
)

__author__ = "E.A. van Valkenburg"
__copyright__ = "E.A. van Valkenburg"
__license__ = "mit"
__version__ = __version__

logging.getLogger(__name__)


class SIAAccount:
    """Class for SIA Account."""

    def __init__(self, account_id: str, key: str = None):
        """Create a SIA Account.

        Arguments:
            account_id {str} -- The account id specified by the alarm system, should be 3-16 characters hexadecimal.

        Keyword Arguments:
            key {str} -- The encryption key specified by the alarm system, should be 16,24 or 32 characters hexadecimal. (default: {None})

        """
        SIAAccount.validate_account(account_id, key)
        self.account_id = account_id
        self.key = key.encode("UTF-8") if key else key
        self.encrypted = True if self.key else False
        self.decrypter = self._create_decrypter()
        self.ending = self._create_ending()

    def _create_decrypter(self) -> AES:
        """Create the decrypter function.

        Raises:
            InvalidKeyLengthError: if the key is not a proper string raise this error.

        Returns:
            AES -- AES object

        """
        if self.key:
            try:
                return AES.new(
                    self.key,
                    AES.MODE_CBC,
                    unhexlify("00000000000000000000000000000000"),
                )
            except ValueError:
                raise InvalidKeyLengthError
        else:
            return None

    def _create_ending(self) -> str:
        """Create the ending of the response acknowledgement message.

        Raises:
            InvalidKeyLengthError: if the key is not a proper string raise this error.

        Returns:
            str -- the ending for acknowledgements.

        """
        if self.key:
            try:
                encrypter = AES.new(
                    self.key, AES.MODE_CBC, Random.new().read(AES.block_size)
                )
                return (
                    hexlify(encrypter.encrypt("00000000000000|]".encode("utf8")))
                    .decode(encoding="UTF-8")
                    .upper()
                )
            except ValueError:
                raise InvalidKeyLengthError
        else:
            return "]"

    def _decrypt_string(self, event: SIAEvent) -> SIAEvent:
        """Decrypt the event, if the account is encrypted, otherwise pass back the event.

        Arguments:
            event {SIAEvent} -- Event to be decrypted.

        Returns:
            SIAEvent -- Event decrypted, with parsed fields.

        """
        if self.encrypted:
            logging.debug("Original: %s", str(event.encrypted_content))
            resmsg = self.decrypter.decrypt(
                unhexlify(event.encrypted_content.encode("utf8"))
            ).decode(encoding="UTF-8", errors="replace")
            logging.debug("Decrypted: %s", resmsg)
            event.content = resmsg
            event.parse_decrypted(resmsg)
        return event

    def __eq__(self, other):
        """To implement 'in' operator"""
        # Comparing with int (assuming "value" is int)
        if isinstance(other, str):
            return self.account_id == other
        # Comparing with another Test object
        elif isinstance(other, SIAAccount):
            return self.account_id == other.account_id

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
