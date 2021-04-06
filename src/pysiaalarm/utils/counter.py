"""Counter helper class."""
from dataclasses import dataclass
from typing import Optional

from ..const import (
    COUNTER_ACCOUNT,
    COUNTER_CODE,
    COUNTER_CRC,
    COUNTER_EVENTS,
    COUNTER_FORMAT,
    COUNTER_TIMESTAMP,
    COUNTER_USER_CODE,
    COUNTER_VALID,
)


@dataclass
class Counter:
    """Class for the counter."""

    error_account: int = 0
    error_code: int = 0
    error_crc: int = 0
    error_format: int = 0
    error_timestamp: int = 0
    error_user_function: int = 0
    events: int = 0
    valid_events: int = 0

    def increment_error_account(self) -> None:
        """Increment the error_account count."""
        self.error_account += 1

    def increment_error_code(self) -> None:
        """Increment the error_code count."""
        self.error_code += 1

    def increment_error_crc(self) -> None:
        """Increment the error_crc count."""
        self.error_crc += 1

    def increment_error_format(self) -> None:
        """Increment the error_format count."""
        self.error_format += 1

    def increment_error_timestamp(self) -> None:
        """Increment the error_timestamp count."""
        self.error_timestamp += 1

    def increment_error_user_function(self) -> None:
        """Increment the error_user_function count."""
        self.error_user_function += 1

    def increment_events(self) -> None:
        """Increment the events count."""
        self.events += 1

    def increment_valid_events(self) -> None:
        """Increment the valid_events count."""
        self.valid_events += 1

    def get(self, item: str) -> Optional[int]:
        """Get the right counter."""
        if item == COUNTER_ACCOUNT:
            return self.error_account
        if item == COUNTER_CODE:
            return self.error_code
        if item == COUNTER_CRC:
            return self.error_crc
        if item == COUNTER_FORMAT:
            return self.error_format
        if item == COUNTER_TIMESTAMP:
            return self.error_timestamp
        if item == COUNTER_USER_CODE:
            return self.error_user_function
        if item == COUNTER_VALID:
            return self.valid_events
        if item == COUNTER_EVENTS:
            return self.events
        return None  # pragma: no cover

    def increment(self, item: str) -> None:  # pragma: no cover
        """Increment the right counter."""
        if item == COUNTER_ACCOUNT:
            self.increment_error_account()
            return
        if item == COUNTER_CODE:
            self.increment_error_code()
            return
        if item == COUNTER_CRC:
            self.increment_error_crc()
            return
        if item == COUNTER_FORMAT:
            self.increment_error_format()
            return
        if item == COUNTER_TIMESTAMP:
            self.increment_error_timestamp()
            return
        if item == COUNTER_USER_CODE:
            self.increment_error_user_function()
            return
        if item == COUNTER_VALID:
            self.increment_valid_events()
            return
        if item == COUNTER_EVENTS:
            self.increment_events()
