# -*- coding: utf-8 -*-
"""This is the class for the actual TCP handler override of the handle method."""
import logging
from socketserver import BaseRequestHandler
from socketserver import ThreadingTCPServer
from typing import Callable
from typing import Dict

from pysiaalarm.sia_account import SIAAccount
from pysiaalarm.sia_account import SIAResponseType as resp
from pysiaalarm.sia_errors import EventFormatError
from pysiaalarm.sia_errors import ReceivedAccountUnknownError
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
                    logging.debug("Incoming line: %s", line.decode())
                    try:
                        event = None
                        account = None
                        event = SIAEvent(line.decode())
                        if event.valid_message:
                            account = self.server.accounts.get(event.account)
                            if account:
                                event = account.decrypt(event)
                                logging.debug(
                                    "Parsed and decrypted (if applicable) event: %s.",
                                    event,
                                )
                                if not event.valid_timestamp(account.allowed_timeband):
                                    response = resp.NAK
                                    logging.warning(
                                        "Event timestamp is no longer valid: %s",
                                        event.timestamp,
                                    )
                                    self.server.error_count["timestamp"] = (
                                        self.server.error_count["timestamp"] + 1
                                    )
                                elif event.code_not_found:
                                    response = resp.DUH
                                    logging.warning(
                                        "Code not found, replying with DUH to account: %s",
                                        event.account,
                                    )
                                    self.server.error_count["code"] = (
                                        self.server.error_count["code"] + 1
                                    )
                                else:
                                    response = resp.ACK
                            else:
                                response = resp.NAK
                                logging.warning(
                                    "Unknown or non-existing account was used by the event: %s",
                                    event,
                                )
                                self.server.error_count["account"] = (
                                    self.server.error_count["account"] + 1
                                )
                        else:
                            response = None
                            logging.warning("CRC mismatch, ignoring message.")
                            self.server.error_count["crc"] = (
                                self.server.error_count["crc"] + 1
                            )
                    except EventFormatError as exp:
                        response = resp.NAK
                        account = None
                        logging.warning("Last line: %s gave error: %s.", line, exp)
                        self.server.error_count["format"] = (
                            self.server.error_count["format"] + 1
                        )
                    finally:
                        if not account:
                            account_id = ""
                            if event:
                                account_id = event.account
                            account = SIAAccount(account_id)
                        self.respond(account.create_response(event, response))
                    if event and response == resp.ACK:
                        try:
                            self.server.func(event)
                        except Exception as exp:
                            logging.warning(
                                "Last event: %s, gave error in user function: %s.",
                                event,
                                exp,
                            )
                else:
                    break

    def respond(self, response=None):
        """Respond to the client."""
        if response:
            header = ("%04x" % len(response)).upper()
            res = f"\n{SIAEvent.crc_calc(response)}{header}{response}\r"
            self.request.sendall(str.encode(res))
        else:
            self.request.sendall(b"\n\r")
