"""This is a the main class for the SIA Client."""
from __future__ import annotations

import asyncio
import logging
from types import TracebackType
from typing import Any, Callable, Dict, List, Optional, Type

from .. import __author__, __copyright__, __license__, __version__
from ..account import SIAAccount
from ..base_client import BaseSIAClient
from ..event import SIAEvent
from ..utils import CommunicationsProtocol
from .server import SIAServer

_LOGGER = logging.getLogger(__name__)


class SIAClient(BaseSIAClient):
    """Class for Async SIA Client."""

    def __init__(
        self,
        host: str,
        port: int,
        accounts: List[SIAAccount],
        function: Callable[[SIAEvent], None],
        protocol: CommunicationsProtocol = CommunicationsProtocol.TCP,
    ):
        """Create the asynchronous SIA Client object.

        Arguments:
            host {str} -- Host to run the server on, usually would be ""
            port {int} -- The port the server listens to.
            accounts {List[SIAAccount]} -- List of SIA Accounts to add.
            function {Callable[[SIAEvent], None]} -- The function that gets called for each event, can be a asyncio coroutine, otherwise the function gets wrapped to be non-blocking.
            protocol {CommunicationsProtocol Enum} -- CommunicationsProtocol to use, TCP or UDP.

        """
        if not asyncio.iscoroutinefunction(function):
            raise TypeError("Function should be a coroutine, create with async def.")
        BaseSIAClient.__init__(self, host, port, accounts, function, protocol)
        self.task: Any = None
        self.transport: Any = None
        self.dgprotocol: Any = None
        self.sia_server: Any = None
        if self.protocol == CommunicationsProtocol.TCP:
            self.sia_server = SIAServer(self._accounts, self._func, self._counts)

    async def __aenter__(self, **kwargs: Dict[str, Any]) -> SIAClient:
        """Start with as context manager."""
        await self.start(**kwargs)
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> Optional[bool]:
        """End as context manager."""
        await self.stop()
        return True

    async def start(self, **kwargs: Any) -> None:
        """Start the asynchronous SIA server.

        The rest of the arguments are passed directly to asyncio.start_server().

        """
        _LOGGER.debug("Starting SIA.")
        if self.protocol == CommunicationsProtocol.TCP:
            self.coro = asyncio.start_server(
                self.sia_server.handle_line, self._host, self._port, **kwargs
            )
            self.task = asyncio.create_task(self.coro)
            return
        loop = asyncio.get_running_loop()
        self.transport, self.dgprotocol = await loop.create_datagram_endpoint(
            lambda: SIAServer(self._accounts, self._func, self._counts),
            local_addr=(self._host, self._port),
            **kwargs,
        )
        return

    async def stop(self) -> None:
        """Stop the asynchronous SIA server."""
        _LOGGER.debug("Stopping SIA.")
        if self.transport is not None:
            self.transport.close()
            return
        if self.sia_server is not None:
            self.sia_server.shutdown_flag = True
        if self.task is not None:  # pragma: no cover
            await asyncio.gather(self.task)
