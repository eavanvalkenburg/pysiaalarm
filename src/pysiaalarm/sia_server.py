"""This is the class for the actual TCP handler override of the handle method."""
from enum import IntFlag
import logging
from socketserver import BaseRequestHandler, ThreadingTCPServer, ThreadingUDPServer
from typing import Callable, Dict, Tuple

from . import __author__, __copyright__, __license__, __version__
from .base_sia_server import BaseSIAServer
from .sia_account import SIAAccount
from .sia_account import SIAResponseType as resp
from .sia_event import SIAEvent

_LOGGER = logging.getLogger(__name__)


class SIAServer(ThreadingTCPServer, BaseSIAServer):
    """Class for a threaded SIA TCP Server."""

    daemon_threads = True
    allow_reuse_address = True

    def __init__(
        self,
        server_address: Tuple[str, int],
        accounts: Dict[str, SIAAccount],
        func: Callable[[SIAEvent], None],
        counts: Dict,
    ):
        """Create a SIA TCP Server.

        Arguments:
            server_address Tuple[string, int] -- the address the server should listen on.
            accounts Dict[str, SIAAccount] -- accounts as dict with account_id as key, SIAAccount object as value.
            func Callable[[SIAEvent], None] -- Function called for each valid SIA event, that can be matched to a account.
            counts Dict -- counter kept by client to give insights in how many errorous events were discarded of each type.

        """
        ThreadingTCPServer.__init__(self, server_address, SIATCPHandler)
        BaseSIAServer.__init__(self, accounts, func, counts)


class SIAUDPServer(ThreadingUDPServer, BaseSIAServer):
    """Class for a threaded SIA UDP Server."""

    daemon_threads = True
    allow_reuse_address = True

    def __init__(
        self,
        server_address: Tuple[str, int],
        accounts: Dict[str, SIAAccount],
        func: Callable[[SIAEvent], None],
        counts: Dict,
    ):
        """Create a SIA UDP Server.

        Arguments:
            server_address Tuple[string, int] -- the address the server should listen on.
            accounts Dict[str, SIAAccount] -- accounts as dict with account_id as key, SIAAccount object as value.
            func Callable[[SIAEvent], None] -- Function called for each valid SIA event, that can be matched to a account.
            counts Dict -- counter kept by client to give insights in how many errorous events were discarded of each type.

        """
        ThreadingUDPServer.__init__(self, server_address, SIAUDPHandler)
        BaseSIAServer.__init__(self, accounts, func, counts)


class BaseSIAHandler(BaseRequestHandler):
    """Base case for Request handling."""

    _received_data = "".encode()

    def handle_raw_line(self, raw):
        """Handle the line."""
        while len(raw) > 0:  # True and not self.server.shutdown_flag:
            splitter = raw.find(b"\r")
            if splitter == -1:
                line = raw
                raw = ""
                # break
            else:
                line = raw[1:splitter]
                raw = raw[splitter + 1 :]
            decoded_line = line.decode("ascii", errors="ignore")
            _LOGGER.debug("Incoming line: %s", decoded_line)
            self.server.counts["events"] = self.server.counts["events"] + 1
            event, account, response = self.server.parse_and_check_event(decoded_line)
            self.respond(event, account, response)
            # check for event and if the response is acknowledge, which means the event is valid.
            if event and response == resp.ACK:
                self.server.func_wrap(event)

    def respond(self, event, account, response):
        """Abstract method for responding."""
        pass


class SIATCPHandler(BaseSIAHandler):
    """Class for TCP Handling."""

    def handle(self):
        """Overwritten method for the RequestHandler."""
        while True and not self.server.shutdown_flag:
            raw = self.request.recv(1024)
            if not raw:
                break
            raw = bytearray(raw)
            self.handle_raw_line(raw)

    def respond(self, event, account, response):
        """Respond to the event."""
        try:
            self.request.sendall(account.create_response(event, response))
        except Exception as exp:
            _LOGGER.error(
                "Exception caught while responding to event: %s, exception: %s",
                event,
                exp,
            )


class SIAUDPHandler(BaseSIAHandler):
    """Class for UDP Handling."""

    def handle(self):
        """Overwritten method for the RequestHandler."""
        if not self.server.shutdown_flag:
            raw = self.request[0]
            # socket = self.request[1]
            if raw:
                raw = bytearray(raw)
                self.handle_raw_line(raw)

    def respond(self, event, account, response):
        """Respond to the event."""
        try:
            self.request[1].sendto(
                account.create_response(event, response), self.client_address
            )
        except Exception as exp:
            _LOGGER.error(
                "Exception caught while responding to event: %s, exception: %s",
                event,
                exp,
            )
