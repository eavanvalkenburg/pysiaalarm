"""This is a the main class for the SIA Client."""
import asyncio
import logging
from typing import Callable, List

from .. import __author__, __copyright__, __license__, __version__
from ..base_sia_client import BaseSIAClient
from ..sia_account import SIAAccount
from ..sia_event import SIAEvent
from .sia_server import SIAServer
from ..sia_const import Protocol

_LOGGER = logging.getLogger(__name__)


class SIAClient(BaseSIAClient):
    """Class for Async SIA Client."""

    def __init__(
        self,
        host: str,
        port: int,
        accounts: List[SIAAccount],
        function: Callable[[SIAEvent], None],
        protocol: Protocol = Protocol.TCP,
    ):
        """Create the asynchronous SIA Client object.

        Arguments:
            host {str} -- Host to run the server on, usually would be ""
            port {int} -- The port the server listens to.
            accounts {List[SIAAccount]} -- List of SIA Accounts to add.
            function {Callable[[SIAEvent], None]} -- The function that gets called for each event, can be a asyncio coroutine, otherwise the function gets wrapped to be non-blocking.
            protocol {Protocol Enum} -- Protocol to use, TCP or UDP.

        """
        if not asyncio.iscoroutinefunction(function):
            raise TypeError("Function should be a coroutine, create with async def.")
        BaseSIAClient.__init__(self, host, port, accounts, function, protocol)
        self.task = None
        self.transport = None
        self.dgprotocol = None
        self.sia_server = None
        if self.protocol == Protocol.TCP:
            self.sia_server = SIAServer(self._accounts, self._func, self._counts)

    async def __aenter__(self, **kwargs):
        """Start with as context manager."""
        await self.start(**kwargs)
        return self

    async def __aexit__(self, type, value, tb):
        """End as context manager."""
        await self.stop()

    async def start(self, **kwargs):
        """Start the asynchronous SIA server.

        The rest of the arguments are passed directly to asyncio.start_server().

        """
        _LOGGER.debug("Starting SIA.")
        if self.protocol == Protocol.TCP:
            self.coro = asyncio.start_server(
                self.sia_server.handle_line, self._host, self._port, **kwargs
            )
            self.task = asyncio.create_task(self.coro)
        else:
            loop = asyncio.get_running_loop()
            self.transport, self.dgprotocol = await loop.create_datagram_endpoint(
                lambda: SIAServer(self._accounts, self._func, self._counts),
                local_addr=(self._host, self._port),
                **kwargs,
            )

    async def stop(self):
        """Stop the asynchronous SIA server."""
        _LOGGER.debug("Stopping SIA.")
        if self.protocol == Protocol.TCP:
            self.sia_server.shutdown_flag = True
            if self.task:
                await self.task
        else:
            self.transport.close()
