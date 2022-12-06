"""This is the base class with the handling logic for both sia_servers."""
from __future__ import annotations

import logging
from abc import ABC
from collections.abc import Awaitable, Callable

from .account import SIAAccount
from .const import (
    COUNTER_ACCOUNT,
    COUNTER_CODE,
    COUNTER_CRC,
    COUNTER_EVENTS,
    COUNTER_FORMAT,
    COUNTER_TIMESTAMP,
    COUNTER_USER_CODE,
)
from .errors import EventFormatError, NoAccountError
from .event import NAKEvent, OHEvent, SIAEvent, EventsType
from .utils import Counter, ResponseType

_LOGGER = logging.getLogger(__name__)


class BaseSIAServer(ABC):
    """Base class for SIA Server."""

    def __init__(
        self,
        accounts: dict[str, SIAAccount],
        counts: Counter,
        func: Callable[[SIAEvent], None] | None = None,
        async_func: Callable[[SIAEvent], Awaitable[None]] | None = None,
    ):
        """Create a SIA Server.

        Arguments:
            accounts Dict[str, SIAAccount] -- accounts as dict with account_id as key, SIAAccount object as value.  # pylint: disable=line-too-long
            func Callable[[SIAEvent], None] -- Function called for each valid SIA event, that can be matched to a account.  # pylint: disable=line-too-long
            counts Counter -- counter kept by client to give insights in how many errorous EventsType were discarded of each type.  # pylint: disable=line-too-long
        """
        self.accounts = accounts
        self.func = func
        self.async_func = async_func
        self.counts = counts
        self.shutdown_flag = False

    def parse_and_check_event(self, line: bytes) -> EventsType | None:
        """Parse and check the line and create the event, check the account and define the response.

        Args:
            line (bytes): Line to parse

        Returns:
            SIAEvent: The SIAEvent type of the parsed line.
            ResponseType: The response to send to the alarm.

        """
        if not line.strip():
            return None
        self.log_and_count(COUNTER_EVENTS, line=line)
        try:
            event = SIAEvent.from_line(line, self.accounts)
        except NoAccountError as exc:
            self.log_and_count(COUNTER_ACCOUNT, line, exception=exc)
            binary_crc = NAKEvent.check_crc_type(line)
            return NAKEvent(binary_crc=binary_crc)
        except EventFormatError as exc:
            self.log_and_count(COUNTER_FORMAT, line, exception=exc)
            binary_crc = NAKEvent.check_crc_type(line)
            return NAKEvent(binary_crc=binary_crc)

        if isinstance(event, OHEvent):
            return event  # pragma: no cover
        if not event.valid_message:
            self.log_and_count(COUNTER_CRC, event=event)
        elif not event.sia_account:
            self.log_and_count(COUNTER_ACCOUNT, event=event)
        elif event.code_not_found:
            self.log_and_count(COUNTER_CODE, event=event)
        elif not event.valid_timestamp:
            self.log_and_count(COUNTER_TIMESTAMP, event=event)
        return event

    async def async_func_wrap(self, event: EventsType | None) -> None:
        """Wrap the user function in a try."""
        if (
            event is None
            or not (isinstance(event, SIAEvent))
            or event.response != ResponseType.ACK
        ):
            return
        self.counts.increment_valid_events()
        try:
            assert self.async_func is not None
            await self.async_func(event)  # type: ignore
        except Exception as exp:  # pylint: disable=broad-except
            self.log_and_count(COUNTER_USER_CODE, event=event, exception=exp)

    def func_wrap(self, event: EventsType | None) -> None:
        """Wrap the user function in a try."""
        if (
            event is None
            or not (isinstance(event, SIAEvent))
            or event.response != ResponseType.ACK
        ):
            return
        self.counts.increment_valid_events()
        try:
            assert self.func is not None
            self.func(event)
        except Exception as exp:  # pylint: disable=broad-except
            self.log_and_count(COUNTER_USER_CODE, event=event, exception=exp)

    def log_and_count(
        self,
        counter: str,
        line: str | bytes | None = None,
        event: SIAEvent | None = None,
        exception: Exception | None = None,
    ) -> None:
        """Log the appropriate line and increment the right counter."""
        if counter == COUNTER_ACCOUNT and exception is not None:
            _LOGGER.warning(
                "There is no account for a encrypted line, line was: %s",
                line,
            )
        if counter == COUNTER_ACCOUNT and event:
            _LOGGER.warning(
                "Unknown or non-existing account (%s) was used by the event: %s",
                event.account,
                event,
            )
        if counter == COUNTER_FORMAT and exception:
            _LOGGER.warning(
                "Last line could not be parsed succesfully. Error message: %s. Line: %s",
                exception.args[0],
                line,
            )
        if counter == COUNTER_USER_CODE and event and exception:
            _LOGGER.warning(
                "Last event: %s, gave error in user function: %s.", event, exception
            )
        if counter == COUNTER_CRC and event:
            _LOGGER.warning(
                "CRC mismatch, ignoring message. Sent CRC: %s, Calculated CRC: %s. Line was %s",
                event.msg_crc,
                event.calc_crc,
                event.full_message,
            )
        if counter == COUNTER_CODE and event:
            _LOGGER.warning(
                "Code not found, replying with DUH to account: %s", event.account
            )
        if counter == COUNTER_TIMESTAMP and event:
            _LOGGER.warning("Event timestamp is no longer valid: %s", event.timestamp)
        if counter == COUNTER_EVENTS and line:
            _LOGGER.debug("Incoming line: %s", line)
        self.counts.increment(counter)
