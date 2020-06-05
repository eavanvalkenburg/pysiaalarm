# -*- coding: utf-8 -*-
"""This is a the main class for the SIA Client."""
import asyncio
import logging
import socket
from threading import Thread
from typing import Callable
from typing import Coroutine
from typing import List
from typing import Union

from . import __author__
from . import __copyright__
from . import __license__
from . import __version__
from .base_sia_client import BaseSIAClient
from .sia_account import SIAAccount
from .sia_event import SIAEvent
from .sia_server import SIAServer

logging.getLogger(__name__)


class SIAClient(Thread, BaseSIAClient):
    def __init__(
        self,
        host: str,
        port: int,
        accounts: List[SIAAccount],
        function: Callable[[SIAEvent], None],
    ):
        """Create the threaded SIA Client object.

        Arguments:
            host {str} -- Host to run the server on, usually would be ""
            port {int} -- The port the server listens to.
            accounts {List[SIAAccount]} -- List of SIA Accounts to add.
            function {Callable[[SIAEvent], None]} -- The function that gets called for each event.

        """
        if asyncio.iscoroutinefunction(function):
            raise TypeError(
                "Asyncio coroutines as the function are not supported, please use the aio version of the SIAClient for that."
            )
        Thread.__init__(self)
        BaseSIAClient.__init__(self, host, port, accounts, function)
        self.sia_server = SIAServer(
            (self._host, self._port), self._accounts, self._func, self._counts
        )

    def start(self):
        """Start the SIA TCP Handler thread."""
        logging.debug("Starting SIA.")
        self.server_thread = Thread(target=self.sia_server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()

    def stop(self):
        """Stop the SIA TCP Handler thread."""
        logging.debug("Stopping SIA.")
        self.sia_server.shutdown_flag = True
        self.sia_server.shutdown()
        self.sia_server.server_close()
        self.server_thread.join()
