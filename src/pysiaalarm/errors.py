"""Errors for SIA Server."""


class InvalidKeyFormatError(Exception):
    """Error for when the key is not a hex string."""

    pass


class InvalidKeyLengthError(Exception):
    """Error for when the key is not the right amount of characters."""

    pass


class InvalidAccountFormatError(Exception):
    """Error for when the account is not a hex string."""

    pass


class InvalidAccountLengthError(Exception):
    """Error for when the key is not the right amount of characters."""

    pass


class EventFormatError(Exception):
    """Error for when a event is incorrectly formatted."""

    pass


class EventCRCError(Exception):
    """Error for when a event hass a mismatched CRC."""

    pass
