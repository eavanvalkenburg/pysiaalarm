"""This is the base class with the handling logic for both sia_servers."""
import logging
import re
from abc import ABC
from typing import Callable, Dict, Tuple

from .sia_account import SIAAccount, SIAResponseType
from .sia_errors import EventFormatError
from .sia_event import SIAEvent

_LOGGER = logging.getLogger(__name__)

# sample OH: SR0001L0001    006969XX    [ID00000000]
oh_regex = r"""
^S
(?:R)(?:(?<=R)(?:\d{4}))
(?:L)(?:(?<=L)(?:\d{4}))
\s+\w{8}\s+
\[(?:\w+)\]$
"""
OH_MATCHER = re.compile(oh_regex, re.X)


class BaseSIAServer(ABC):
    """Base class for SIA Server."""

    def __init__(
        self,
        accounts: Dict[str, SIAAccount],
        func: Callable[[SIAEvent], None],
        counts: Dict,
    ):
        """Create a SIA Server.

        Arguments:
            accounts Dict[str, SIAAccount] -- accounts as dict with account_id as key, SIAAccount object as value.
            func Callable[[SIAEvent], None] -- Function called for each valid SIA event, that can be matched to a account.
            counts Dict -- counter kept by client to give insights in how many errorous events were discarded of each type.

        """
        self.accounts = accounts
        self.func = func
        self.counts = counts
        self.shutdown_flag = False

    def parse_and_check_event(
        self, line: str
    ) -> Tuple[SIAEvent, SIAAccount, SIAResponseType]:
        """Parse and check the line and create the event, check the account and define the response.

        Args:
            line (str): Line to parse

        Returns:
            SIAEvent: The SIAEvent type of the parsed line.
            SIAAccount: The SIAAccount the line came from.
            SIAResponseType: The response to send to the alarm.

        """
        try:
            event = SIAEvent(line)
            # TODO: add heartbeat handle return Event, None, ACK
        except EventFormatError as e:
            try:
                _LOGGER.debug("Not a SIA Event, checking OH.")
                oh_event = OH_MATCHER.match(line)
                if oh_event:
                    return None, None, SIAResponseType.ACK
                else:
                    raise EventFormatError from e
            except EventFormatError:
                self.counts["errors"]["format"] = self.counts["errors"]["format"] + 1
                _LOGGER.warning(
                    "Last line could not be parsed as a SIAEvent or OHEvent, line was: %s",
                    line,
                )
                return None, None, SIAResponseType.NAK

        if not event.valid_message:
            self.counts["errors"]["crc"] = self.counts["errors"]["crc"] + 1
            _LOGGER.warning(
                "CRC mismatch, ignoring message. Sent CRC: %s, Calculated CRC: %s. Line was %s",
                event.msg_crc,
                event.calc_crc,
                line,
            )
            return event, SIAAccount(event.account), None

        account = self.accounts.get(event.account)
        if not account:
            self.counts["errors"]["account"] = self.counts["errors"]["account"] + 1
            _LOGGER.warning(
                "Unknown or non-existing account (%s) was used by the event: %s",
                event.account,
                event,
            )
            return event, SIAAccount(event.account), SIAResponseType.NAK

        try:
            event = account.decrypt(event)
        except EventFormatError:
            self.counts["errors"]["format"] = self.counts["errors"]["format"] + 1
            _LOGGER.warning(
                "Decrypting last line: %s could not be parsed as a SIAEvent, content: %s",
                line,
                event.content,
            )
            return None, None, SIAResponseType.NAK

        _LOGGER.debug("Parsed event: %s.", event)

        if event.code_not_found and event.message_type == "SIA-DCS":
            self.counts["errors"]["code"] = self.counts["errors"]["code"] + 1
            _LOGGER.warning(
                "Code not found, replying with DUH to account: %s", event.account
            )
            return event, account, SIAResponseType.DUH

        if not event.valid_timestamp(account.allowed_timeband):
            self.counts["errors"]["timestamp"] = self.counts["errors"]["timestamp"] + 1
            _LOGGER.warning("Event timestamp is no longer valid: %s", event.timestamp)
            return event, account, SIAResponseType.NAK

        return event, account, SIAResponseType.ACK
