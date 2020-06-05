# -*- coding: utf-8 -*-
"""This is the class for the actual TCP handler override of the handle method."""
import logging
from socketserver import BaseRequestHandler
from socketserver import ThreadingTCPServer
from typing import Callable
from typing import Coroutine
from typing import Dict
from typing import Union

from . import __author__
from . import __copyright__
from . import __license__
from . import __version__
from .base_sia_server import BaseSIAServer
from .sia_account import SIAAccount
from .sia_account import SIAResponseType as resp
from .sia_event import SIAEvent

logging.getLogger(__name__)


class SIAServer(ThreadingTCPServer, BaseSIAServer):
    """Class for a threaded SIA Server."""

    daemon_threads = True
    allow_reuse_address = True

    def __init__(
        self,
        server_address: (str, int),
        accounts: Dict[str, SIAAccount],
        func: Callable[[SIAEvent], None],
        counts: Dict,
    ):
        """Create a SIA Server.

        Arguments:
            server_address {tuple(string, int)} -- the address the server should listen on.
            accounts Dict[str, SIAAccount] -- accounts as dict with account_id as key, SIAAccount object as value.
            func Callable[[SIAEvent], None] -- Function called for each valid SIA event, that can be matched to a account.
            counts Dict -- counter kept by client to give insights in how many errorous events were discarded of each type.

        """
        ThreadingTCPServer.__init__(self, server_address, SIATCPHandler)
        BaseSIAServer.__init__(self, accounts, func, counts)


class SIATCPHandler(BaseRequestHandler):
    _received_data = "".encode()

    def handle(self):
        """Overwritten method for the RequestHandler."""
        while True and not self.server.shutdown_flag:
            raw = self.request.recv(1024)
            if not raw:
                return
            raw = bytearray(raw)
            while True and not self.server.shutdown_flag:
                splitter = raw.find(b"\r")
                if splitter == -1:
                    break
                line = raw[1:splitter]
                raw = raw[splitter + 1 :]
                decoded_line = line.decode()
                logging.debug("Incoming line: %s", decoded_line)
                self.server.counts["events"] = self.server.counts["events"] + 1
                event, account, response = self.server.parse_and_check_event(
                    decoded_line
                )

                self.request.sendall(account.create_response(event, response))
                # check for event and if the response is acknowledge, which means the event is valid.
                if event and response == resp.ACK:
                    self.server.counts["valid_events"] = (
                        self.server.counts["valid_events"] + 1
                    )
                    try:
                        self.server.func(event)
                    except Exception as exp:
                        logging.warning(
                            "Last event: %s, gave error in user function: %s.",
                            event,
                            exp,
                        )
                        self.server.counts["errors"]["user_code"] = (
                            self.server.counts["errors"]["user_code"] + 1
                        )
