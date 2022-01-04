"""This is the base class with the handling logic for both sia_servers."""
import asyncio
import logging
from abc import ABC
from typing import Awaitable, Callable, Dict, Union

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
from .event import NAKEvent, OHEvent, SIAEvent
from .utils import Counter

_LOGGER = logging.getLogger(__name__)


class BaseSIAServer(ABC):
    """Base class for SIA Server."""

    def __init__(
        self,
        accounts: Dict[str, SIAAccount],
        func: Union[Callable[[SIAEvent], Awaitable[None]], Callable[[SIAEvent], None]],
        counts: Counter,
        binary_crc: bool = False,
    ):
        """Create a SIA Server.

        Arguments:
            accounts Dict[str, SIAAccount] -- accounts as dict with account_id as key, SIAAccount object as value.
            func Callable[[SIAEvent], None] -- Function called for each valid SIA event, that can be matched to a account.
            counts Counter -- counter kept by client to give insights in how many errorous events were discarded of each type.
            binary_crc bool -- set to True if your system sends CRC in binary instead of hex
        """
        self.accounts = accounts
        self.func = func
        self.counts = counts
        self.shutdown_flag = False
        self.binary_crc = binary_crc

    def parse_and_check_event(self, data: bytes) -> Union[SIAEvent, OHEvent, NAKEvent]:
        """Parse and check the data and create the event, check the account and define the response.

        Args:
            data (bytes): Data to parse

        Returns:
            SIAEvent: The SIAEvent type of the parsed line.
            ResponseType: The response to send to the alarm.

        """
        self.log_and_count(COUNTER_EVENTS, data=data)
        try:
            event = SIAEvent.from_message(data, self.accounts, self.binary_crc)
        except NoAccountError as exc:
            self.log_and_count(COUNTER_ACCOUNT, data, exception=exc)
            return NAKEvent(is_binary_crc=self.binary_crc)
        except EventFormatError as exc:
            self.log_and_count(COUNTER_FORMAT, data, exception=exc)
            return NAKEvent(is_binary_crc=self.binary_crc)

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

    async def async_func_wrap(self, event: SIAEvent) -> None:
        """Wrap the user function in a try."""
        self.counts.increment_valid_events()
        try:
            await self.func(event)  # type: ignore
        except Exception as exp:
            self.log_and_count(COUNTER_USER_CODE, event=event, exception=exp)

    def func_wrap(self, event: SIAEvent) -> None:
        """Wrap the user function in a try."""
        self.counts.increment_valid_events()
        try:
            self.func(event)
        except Exception as exp:
            self.log_and_count(COUNTER_USER_CODE, event=event, exception=exp)

    def log_and_count(
        self,
        counter: str,
        data: bytes = None,
        event: SIAEvent = None,
        exception: Exception = None,
    ) -> None:
        """Log the appropriate line and increment the right counter."""
        if counter == COUNTER_ACCOUNT and exception is not None:
            _LOGGER.warning(
                "There is no account for a encrypted line, line was: %r",
                data,
            )
        if counter == COUNTER_ACCOUNT and event:
            _LOGGER.warning(
                "Unknown or non-existing account (%s) was used by the event: %s",
                event.account,
                event,
            )
        if counter == COUNTER_FORMAT and exception:
            _LOGGER.warning(
                "Last line could not be parsed succesfully. Error message: %s. Line: %r",
                exception.args[0],
                data,
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
        if counter == COUNTER_EVENTS and data:
            _LOGGER.debug("Incoming line: %r", data)
        self.counts.increment(counter)
