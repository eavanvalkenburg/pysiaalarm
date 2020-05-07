# -*- coding: utf-8 -*-
"""This is the class for the actual TCP handler override of the handle method."""
import logging
from socketserver import BaseRequestHandler
from socketserver import ThreadingTCPServer
from typing import Callable
from typing import Dict

from pysiaalarm.sia_account import SIAAccount
from pysiaalarm.sia_account import SIAResponseType as resp
from pysiaalarm.sia_errors import CodeNotFoundError
from pysiaalarm.sia_errors import CRCMismatchError
from pysiaalarm.sia_errors import EventFormatError
from pysiaalarm.sia_errors import ReceivedAccountUnknownError
from pysiaalarm.sia_errors import TimestampError
from pysiaalarm.sia_event import SIAEvent

logging.getLogger(__name__)


class SIAServer(ThreadingTCPServer):
    """Class for a SIA Server."""

    daemon_threads = True
    allow_reuse_address = True

    def __init__(
        self,
        server_address: (str, int),
        accounts: Dict[str, SIAAccount],
        func: Callable[[SIAEvent], None],
        error_count: Dict,
    ):
        """Create a SIA Server.

        Arguments:
            server_address {tuple(string, int)} -- the address the server should listen on.
            accounts Dict[str, SIAAccount] -- accounts as dict with account_id as key, SIAAccount object as value.
            func Callable[[SIAEvent], None] -- Function called for each valid SIA event, that can be matched to a account.
            error_count Dict -- counter kept by client to give insights in how many errorous events were discarded of each type.

        """
        ThreadingTCPServer.__init__(self, server_address, SIATCPHandler)
        self.accounts = accounts
        self.func = func
        self.error_count = error_count


class SIATCPHandler(BaseRequestHandler):
    """Class for the TCP Handler."""

    _received_data = "".encode()

    def handle(self):
        """Overwritten method for the RequestHandler."""
        line = b""
        while True:
            raw = self.request.recv(1024)
            if not raw:
                return
            raw = bytearray(raw)
            while True:
                splitter = raw.find(b"\r")
                if splitter > -1:
                    line = raw[1:splitter]
                    raw = raw[splitter + 1 :]
                    decoded_line = line.decode()
                    logging.debug("Incoming line: %s", decoded_line)
                    self._parse_line(decoded_line)
                else:
                    break

    def _parse_line(self, line):
        """Parse a line as a SIAEvent, match with account, check validity, finally respond.

        Arguments:
            line str -- The line to be parsed.

        """
        event = None
        try:
            # parse as SIAEvent, could throw EventFormatError
            event = SIAEvent(line)

            # check crc, if wrong throw CRCMismatchError
            if not event.valid_message:
                raise CRCMismatchError

            # match to account, if not found throw ReceivedAccountUnknownError
            account = self.server.accounts.get(event.account)
            if not account:
                raise ReceivedAccountUnknownError

            # decrypt, will just return event if not encrypted account.
            event = account.decrypt(event)
            logging.debug("Parsed and decrypted (if applicable) event: %s.", event)

            # check valid timestamp, throw TimestampError if not within Timeband.
            if not event.valid_timestamp(account.allowed_timeband):
                raise TimestampError

            # check if the code is known, throw CodeNotFoundError otherwise.
            if event.code_not_found:
                raise CodeNotFoundError

            # if all good, response with acknowledgement.
            response = resp.ACK
        except EventFormatError:
            response = resp.NAK
            account = SIAAccount("")
            self.server.error_count["format"] = self.server.error_count["format"] + 1
            logging.warning("Last line: %s could not be parsed as a SIAEvent.", line)
        except CRCMismatchError:
            response = None
            account = SIAAccount(event.account)
            self.server.error_count["crc"] = self.server.error_count["crc"] + 1
            logging.warning("CRC mismatch, ignoring message.")
        except ReceivedAccountUnknownError:
            response = resp.NAK
            account = SIAAccount(event.account)
            self.server.error_count["account"] = self.server.error_count["account"] + 1
            logging.warning(
                "Unknown or non-existing account (%s) was used by the event: %s",
                event.account,
                event,
            )
        except TimestampError:
            response = resp.NAK
            self.server.error_count["timestamp"] = (
                self.server.error_count["timestamp"] + 1
            )
            logging.warning("Event timestamp is no longer valid: %s", event.timestamp)
        except CodeNotFoundError:
            response = resp.DUH
            self.server.error_count["code"] = self.server.error_count["code"] + 1
            logging.warning(
                "Code not found, replying with DUH to account: %s", event.account
            )
        finally:
            self.respond(account.create_response(event, response))
            # check for event and if the response is acknowledge, which means the event is valid.
            if event and response == resp.ACK:
                try:
                    self.server.func(event)
                except Exception as exp:
                    logging.warning(
                        "Last event: %s, gave error in user function: %s.", event, exp
                    )

    def respond(self, response=None):
        """Respond to the client."""
        if response:
            header = ("%04x" % len(response)).upper()
            res = f"\n{SIAEvent.crc_calc(response)}{header}{response}\r"
            self.request.sendall(str.encode(res))
        else:
            self.request.sendall(b"\n\r")
