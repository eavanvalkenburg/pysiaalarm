"""This is the class for the actual TCP handler override of the handle method."""
import logging
from socketserver import BaseRequestHandler, ThreadingTCPServer
from typing import Callable, Dict, Tuple

from . import __author__, __copyright__, __license__, __version__
from .base_sia_server import BaseSIAServer
from .sia_account import SIAAccount
from .sia_account import SIAResponseType as resp
from .sia_event import SIAEvent

_LOGGER = logging.getLogger(__name__)


class SIAServer(ThreadingTCPServer, BaseSIAServer):
    """Class for a threaded SIA Server."""

    daemon_threads = True
    allow_reuse_address = True

    def __init__(
        self,
        server_address: Tuple[str, int],
        accounts: Dict[str, SIAAccount],
        func: Callable[[SIAEvent], None],
        counts: Dict,
    ):
        """Create a SIA Server.

        Arguments:
            server_address Tuple[string, int] -- the address the server should listen on.
            accounts Dict[str, SIAAccount] -- accounts as dict with account_id as key, SIAAccount object as value.
            func Callable[[SIAEvent], None] -- Function called for each valid SIA event, that can be matched to a account.
            counts Dict -- counter kept by client to give insights in how many errorous events were discarded of each type.

        """
        ThreadingTCPServer.__init__(self, server_address, SIATCPHandler)
        BaseSIAServer.__init__(self, accounts, func, counts)


class SIATCPHandler(BaseRequestHandler):
    """Class for TCP Handling."""

    _received_data = "".encode()

    def handle(self):
        """Overwritten method for the RequestHandler."""
        while True and not self.server.shutdown_flag:
            raw = self.request.recv(1024)
            if not raw:
                break
            raw = bytearray(raw)
            while len(raw) > 0:  # True and not self.server.shutdown_flag:
                splitter = raw.find(b"\r")
                if splitter == -1:
                    line = raw
                    raw = ""
                    # break
                else:
                    line = raw[1:splitter]
                    raw = raw[splitter + 1 :]
                decoded_line = line.decode("ascii")
                _LOGGER.debug("Incoming line: %s", decoded_line)
                self.server.counts["events"] = self.server.counts["events"] + 1
                event, account, response = self.server.parse_and_check_event(
                    decoded_line
                )
                try:
                    self.request.sendall(account.create_response(event, response))
                except Exception as exp:
                    _LOGGER.warning(
                        "Exception caught while responding to event: %s, exception: %s",
                        event,
                        exp,
                    )
                # check for event and if the response is acknowledge, which means the event is valid.
                if event and response == resp.ACK:
                    self.server.counts["valid_events"] = (
                        self.server.counts["valid_events"] + 1
                    )
                    try:
                        self.server.func(event)
                    except Exception as exp:
                        _LOGGER.warning(
                            "Last event: %s, gave error in user function: %s.",
                            event,
                            exp,
                        )
                        self.server.counts["errors"]["user_code"] = (
                            self.server.counts["errors"]["user_code"] + 1
                        )
