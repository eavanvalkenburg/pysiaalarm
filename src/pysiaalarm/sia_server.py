# -*- coding: utf-8 -*-
"""This is the class for the actual TCP handler override of the handle method."""

import logging
from socketserver import BaseRequestHandler, ThreadingTCPServer
from typing import Callable, Dict

from pysiaalarm.sia_account import SIAAccount
from pysiaalarm.sia_account import SIAResponseType as resp
from pysiaalarm.sia_errors import (
    CRCMismatchError,
    EventFormatError,
    ReceivedAccountUnknownError,
)
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
    ):
        """Create a SIA Server.

        Arguments:
            server_address {tuple(string, int)} -- the address the server should listen on.
            accounts Dict[str, SIAAccount] -- accounts as dict with account_id as key, SIAAccount object as value.
            func Callable[[SIAEvent], None] -- Function called for each valid SIA event, that can be matched to a account.

        """
        ThreadingTCPServer.__init__(self, server_address, SIATCPHandler)
        self.accounts = accounts
        self.func = func

    def handle_error(self, request, client_address):
        """Handle an error gracefully.  May be overridden.

        The default is to print a traceback and continue.

        """
        import traceback

        traceback.print_exc()
        logging.error(
            "Last request %s coming from %s gave an error.", request, client_address
        )


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
                        event = SIAEvent(line.decode())
                        account = self.server.accounts.get(event.account)
                        if account:
                            event = account.decrypt(event)
                            logging.debug(
                                "Parsed and decrypted (if applicable) event: %s.", event
                            )
                            if not event.valid_timestamp(account.allowed_timeband):
                                response = resp.NAK
                                logging.warning(
                                    "Event timestamp is no longer valid: %s",
                                    event.timestamp,
                                )
                            elif event.code_not_found:
                                response = resp.DUH
                                logging.warning(
                                    "Code not found, replying with DUH to account: %s",
                                    event.account,
                                )
                            else:
                                response = resp.ACK
                        else:
                            event = None
                            raise ReceivedAccountUnknownError(
                                "Unknown or non-existing account was used by the event: &s",
                                event,
                            )
                    except CRCMismatchError:
                        response = None
                        account = None
                        logging.warning("CRC mismatch, ignoring message.")
                    except (EventFormatError, ReceivedAccountUnknownError) as exp:
                        response = resp.NAK
                        account = None
                        logging.warning("Last line: %s gave error: %s.", line, exp)
                    finally:
                        if not account:
                            account_id = ""
                            if event:
                                account_id = event.account
                            account = SIAAccount(account_id)
                        self.respond(account.create_response(event, response))
                    if event:
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
        logging.info("Sending response to client: %s", response)
        if response:
            header = ("%04x" % len(response)).upper()
            res = f"\n{SIAEvent.crc_calc(response)}{header}{response}\r"
            self.request.sendall(str.encode(res))
        else:
            self.request.sendall(b"\n\r")
