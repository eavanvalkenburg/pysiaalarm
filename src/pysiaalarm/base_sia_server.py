"""This is the base class with the handling logic for both sia_servers."""
import logging
from abc import ABC
from typing import Callable
from typing import Dict

from .sia_account import SIAAccount
from .sia_account import SIAResponseType
from .sia_errors import EventFormatError
from .sia_event import SIAEvent

logging.getLogger(__name__)


class BaseSIAServer(ABC):
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
    ) -> (SIAEvent, SIAAccount, SIAResponseType):
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
        except EventFormatError:
            logging.warning("Last line: %s could not be parsed as a SIAEvent.", line)
            self.counts["errors"]["format"] = self.counts["errors"]["format"] + 1
            return None, SIAAccount(""), SIAResponseType.NAK

        if not event.valid_message:
            self.counts["errors"]["crc"] = self.counts["errors"]["crc"] + 1
            logging.warning("CRC mismatch, ignoring message.")
            return event, SIAAccount(event.account), None

        account = self.accounts.get(event.account)
        if not account:
            self.counts["errors"]["account"] = self.counts["errors"]["account"] + 1
            logging.warning(
                "Unknown or non-existing account (%s) was used by the event: %s",
                event.account,
                event,
            )
            return event, SIAAccount(event.account), SIAResponseType.NAK
        event = account.decrypt(event)
        logging.debug("Parsed event: %s.", event)

        if event.code_not_found:
            self.counts["errors"]["code"] = self.counts["errors"]["code"] + 1
            logging.warning(
                "Code not found, replying with DUH to account: %s", event.account
            )
            return event, account, SIAResponseType.DUH

        # check valid timestamp, throw TimestampError if not within Timeband.
        if not event.valid_timestamp(account.allowed_timeband):
            self.counts["errors"]["timestamp"] = self.counts["errors"]["timestamp"] + 1
            logging.warning("Event timestamp is no longer valid: %s", event.timestamp)
            return event, account, SIAResponseType.NAK

        return event, account, SIAResponseType.ACK
