# -*- coding: utf-8 -*-
"""This is a the main class for the SIA Client."""
from __future__ import annotations

import asyncio
import logging
from threading import Thread
from types import TracebackType
from typing import Any, Callable, List, Optional, Type

from ..account import SIAAccount
from ..base_client import BaseSIAClient
from ..event import SIAEvent
from ..utils import CommunicationsProtocol
from .server import SIATCPServer, SIAUDPServer

_LOGGER = logging.getLogger(__name__)


class SIAClient(Thread, BaseSIAClient):
    """Class for Sync SIA Client."""

    def __init__(
        self,
        host: str,
        port: int,
        accounts: List[SIAAccount],
        function: Callable[[SIAEvent], None],
        protocol: CommunicationsProtocol = CommunicationsProtocol.TCP,
    ):
        """Create the threaded SIA Client object.

        Arguments:
            host {str} -- Host to run the server on, usually would be ""
            port {int} -- The port the server listens to.
            accounts {List[SIAAccount]} -- List of SIA Accounts to add.
            function {Callable[[SIAEvent], None]} -- The function that gets called for each event.
            protocol {CommunicationsProtocol Enum} -- CommunicationsProtocol to use, TCP or UDP.

        """
        if asyncio.iscoroutinefunction(function):
            raise TypeError(
                "Asyncio coroutines as the function are not supported, please use the aio version of the SIAClient for that."
            )
        Thread.__init__(self)
        BaseSIAClient.__init__(self, host, port, accounts, function, protocol)
        self.set_tcp_server() if self.protocol == CommunicationsProtocol.TCP else self.set_udp_server()

    def set_tcp_server(self) -> None:
        """Set the sia server to a TCP server."""
        self.sia_server = SIATCPServer(  # type: ignore
            (self._host, self._port), self._accounts, self._func, self._counts  # type: ignore
        )

    def set_udp_server(self) -> None:
        """Set the sia server to a UDP server."""
        self.sia_server = SIAUDPServer(  # type: ignore
            (self._host, self._port), self._accounts, self._func, self._counts  # type: ignore
        )

    def __enter__(self) -> SIAClient:
        """Start with as context manager."""
        self.start()
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> Optional[bool]:
        """End as context manager."""
        self.stop()
        return True

    def start(self, **kwargs: Any) -> None:
        """Start the SIA Handler thread."""
        _LOGGER.debug("Starting SIA.")
        if self.sia_server is not None:  # pragma: no cover
            self.server_thread = Thread(
                target=self.sia_server.serve_forever,
                name="SIAServerThread",
                kwargs=kwargs,
            )
            self.server_thread.daemon = True
            self.server_thread.start()

    def stop(self) -> None:
        """Stop the SIA TCP Handler thread."""
        _LOGGER.debug("Stopping SIA.")
        if self.sia_server is not None:  # pragma: no cover
            self.sia_server.shutdown_flag = True
            self.sia_server.shutdown()
            self.sia_server.server_close()
        if self.server_thread is not None:  # pragma: no cover
            self.server_thread.join()
