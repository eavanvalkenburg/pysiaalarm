"""Errors for SIA Server."""


class InvalidKeyFormatError(Exception):
    """Error for when the key is not a hex string."""


class InvalidKeyLengthError(Exception):
    """Error for when the key is not the right amount of characters."""


class InvalidAccountFormatError(Exception):
    """Error for when the account is not a hex string."""


class InvalidAccountLengthError(Exception):
    """Error for when the key is not the right amount of characters."""


class EventFormatError(Exception):
    """Error for when a event is incorrectly formatted."""


class EventCRCError(Exception):
    """Error for when a event hass a mismatched CRC."""


class NoAccountError(Exception):
    """Error for when a account is not present."""
