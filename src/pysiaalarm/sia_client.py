# -*- coding: utf-8 -*-
"""This is a the main class for the SIA Client."""
import logging
import socket
from threading import Thread
from typing import Callable
from typing import List

from pysiaalarm import __version__
from pysiaalarm.sia_account import SIAAccount
from pysiaalarm.sia_errors import PortInUseError
from pysiaalarm.sia_event import SIAEvent
from pysiaalarm.sia_server import SIAServer

__author__ = "E.A. van Valkenburg"
__copyright__ = "E.A. van Valkenburg"
__license__ = "mit"
__version__ = __version__

logging.getLogger(__name__)


class SIAClient(Thread):
    """Class for SIA Clients."""

    def __init__(
        self,
        host: str,
        port: int,
        accounts: List[SIAAccount],
        function: Callable[[SIAEvent], None],
    ):
        """Create the SIA Client object.

        Arguments:
            host {str} -- Host to run the server on, usually would be ""
            port {int} -- The port the server listens to.
            accounts {List[SIAAccount]} -- List of SIA Accounts to add.
            function {Callable[[SIAEvent], None]} -- The function that gets called for each event.

        """
        Thread.__init__(self)
        self._host = host
        self._port = port
        self._accounts = {a.account_id: a for a in accounts}
        self._func = function
        self.server = SIAServer((self._host, self._port), self._accounts, self._func)

    def test_port(self):
        """Test if the port is in use.

        Raises:
            PortInUseError: If the port is in use.

        Returns:
            bool -- True if all good.

        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind((self._host, self._port))
            logging.debug("No error in bind.")
            return True
        except socket.error as exp:
            logging.debug(exp)
            logging.debug("Error in bind.")
            raise PortInUseError
        finally:
            sock.close()

    def start(self):
        """Start the SIA TCP Handler thread."""
        logging.debug("Starting thread.")
        self.server_thread = Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()

    def stop(self):
        """Stop the SIA TCP Handler thread."""
        logging.debug("Stopping thread.")
        self.server.shutdown()
        self.server.server_close()
        self.server_thread.join()
