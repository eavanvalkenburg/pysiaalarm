"""This is the base class with the handling logic for both sia_servers."""
from __future__ import annotations

import logging
import re
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

# Regex to detect the start of a new SIA/ADM frame within a raw TCP line.
# Some panels (notably Ajax Hub and Dahua Airshield) concatenate multiple
# frames in a single TCP packet.
# Pattern matches: CRC(4hex) + LEN(4hex) + "TYPE" + SEQ(4dec) + L[n] + #ACCOUNT
# Example: 12CE0026"NULL"0000L0#CCC
_MULTI_FRAME_RE = re.compile(
    r'(?<![^\s])'           # not preceded by a non-space character
    r'[A-Fa-f0-9]{4}'       # CRC — 4 hex digits
    r'[A-Fa-f0-9]{4}'       # message length — 4 hex digits
    r'"[^"]{2,10}"'          # message type in double quotes
    r'\d{4}'                # sequence number — 4 decimal digits
    r'L\d'                  # receiver prefix, e.g. L0
    r'#[A-Za-z0-9]{3,16}'  # account id
)


def _split_frames(line: str) -> list[str]:
    """Split a decoded TCP line into individual SIA/ADM frames.

    Some alarm panels (notably Ajax Hub and Dahua Airshield) concatenate
    multiple SIA frames in a single TCP packet. This function detects frame
    boundaries using the fixed SIA header structure and returns each frame
    as a separate string.

    If only one (or zero) frame boundaries are found, the original line is
    returned unchanged so that single-frame traffic is completely unaffected.

    Args:
        line: Decoded TCP line, possibly containing multiple concatenated frames.

    Returns:
        List of individual frame strings.
    """
    positions = [m.start() for m in _MULTI_FRAME_RE.finditer(line)]
    if len(positions) <= 1:
        return [line]
    frames: list[str] = []
    for i, pos in enumerate(positions):
        end = positions[i + 1] if i + 1 < len(positions) else len(line)
        frame = line[pos:end].strip()
        if frame:
            frames.append(frame)
    _LOGGER.debug("Split %d frames from multi-frame packet: %s…", len(frames), line[:80])
    return frames


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

    def parse_and_check_event(self, data: bytes) -> EventsType | None:
        """Parse and check the line and create the event, check the account and define the response.

        Handles multi-frame TCP packets by splitting them and processing each
        frame individually. Some panels (e.g. Ajax Hub, Dahua Airshield)
        concatenate multiple SIA frames in a single TCP packet, with only the
        last frame carrying the \\r terminator expected by read_until().

        Args:
            data (bytes): Raw bytes received from the TCP stream.

        Returns:
            EventsType | None: The last successfully parsed event, or None.
        """
        line = str.strip(data.decode("ascii", errors="ignore"))
        if not line:
            return None

        frames = _split_frames(line)

        last_event: EventsType | None = None
        for frame in frames:
            event = self._parse_single_frame(frame)
            if event is not None:
                last_event = event

        return last_event

    def _parse_single_frame(self, line: str) -> EventsType | None:
        """Parse and check a single SIA/ADM frame.

        Frames that do not match any known SIA format (e.g. Ajax NULL/0000
        supervisory heartbeats) are logged at DEBUG level and skipped, rather
        than raising a WARNING for every heartbeat. According to the official
        SIA Java library, NULL with empty content [] is valid SIA, so this
        is a parser limitation rather than a protocol violation.

        Args:
            line (str): A single decoded SIA frame string.

        Returns:
            EventsType | None: The parsed event, or None if the frame is empty.
        """
        self.log_and_count(COUNTER_EVENTS, line=line)
        try:
            event = SIAEvent.from_line(line, self.accounts)
        except NoAccountError as exc:
            self.log_and_count(COUNTER_ACCOUNT, line, exception=exc)
            return NAKEvent()
        except EventFormatError as exc:
            # Log at DEBUG instead of WARNING: some panels (notably Ajax Hub)
            # send supervisory frames using valid SIA format (NULL/0000 with
            # empty content) that the current regex does not yet recognise.
            # These should not flood the logs as errors.
            _LOGGER.debug(
                "Frame could not be parsed, skipping: %s — %s",
                line,
                exc.args[0] if exc.args else exc,
            )
            return None

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
        line: str | None = None,
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
