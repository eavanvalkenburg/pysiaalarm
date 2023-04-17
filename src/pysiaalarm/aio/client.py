"""This is a the main class for the SIA Client."""
from __future__ import annotations

import asyncio
from abc import abstractmethod
import logging
from collections.abc import Awaitable, Callable
from types import TracebackType
from typing import Any, Type

from ..account import SIAAccount
from ..base_client import BaseSIAClient
from ..event import SIAEvent
from ..utils import CommunicationsProtocol
from .server import SIAServerTCP, SIAServerUDP

_LOGGER = logging.getLogger(__name__)


class SIAClient(BaseSIAClient):
    """Class for Async SIA Client."""

    protocol: CommunicationsProtocol

    def __new__(
        cls,
        *args: Any,
        **kwargs: Any,
    ) -> SIAClient:
        """Create the SIA Client object."""
        subclass_map = {
            subclass.protocol: subclass for subclass in cls.__subclasses__()
        }
        protocol = kwargs.pop("protocol", CommunicationsProtocol.TCP)
        subclass = subclass_map[protocol]
        instance = super(SIAClient, subclass).__new__(subclass)
        return instance

    def __init__(
        self,
        host: str,
        port: int,
        accounts: list[SIAAccount],
        function: Callable[[SIAEvent], Awaitable[None]],
        **kwargs: Any,
    ):
        """Create the asynchronous SIA Client object.

        Arguments:
            host {str} -- Host to run the server on, usually would be ""
            port {int} -- The port the server listens to.
            accounts {List[SIAAccount]} -- List of SIA Accounts to add.
            function {Callable[[SIAEvent], Awaitable[None]]} -- The async function that gets called for each event.  # pylint: disable=line-too-long
            protocol {CommunicationsProtocol Enum} -- CommunicationsProtocol to use, TCP or UDP.

        """
        if not asyncio.iscoroutinefunction(function):
            raise TypeError("Function should be a coroutine, create with async def.")
        BaseSIAClient.__init__(self, host, port, accounts, self.protocol)
        self._func = function

    async def __aenter__(self, **kwargs: Any) -> SIAClient:
        """Start with as context manager."""
        await self.async_start(**kwargs)
        return self

    async def __aexit__(
        self,
        exc_type: Type[BaseException] | None,
        exc_val: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        """End as context manager."""
        await self.async_stop()
        return True

    @abstractmethod
    async def async_start(self, **kwargs: Any) -> None:
        """Start the asynchronous SIA server."""
        pass

    @abstractmethod
    async def async_stop(self) -> None:
        """Stop the asynchronous SIA server."""
        pass

    async def start(self, **kwargs: Any) -> None:
        """Use async_start instead, this method is depricated and will be removed."""
        _LOGGER.warning(
            "This method is depricated and will be removed, use async_start instead."
        )
        await self.async_start(**kwargs)

    async def stop(self) -> None:
        """Use async_stop instead, this method is depricated and will be removed."""
        _LOGGER.warning(
            "This method is depricated and will be removed, use async_stop instead."
        )
        await self.async_stop()


class SIAClientTCP(SIAClient):
    """TCP subclass."""

    protocol = CommunicationsProtocol.TCP

    def __init__(
        self,
        host: str,
        port: int,
        accounts: list[SIAAccount],
        function: Callable[[SIAEvent], Awaitable[None]],
        **kwargs: Any,
    ) -> None:
        """Create the TCP SIA Client object."""
        super().__init__(host, port, accounts, function)
        self.task: asyncio.Task | None = None
        self.sia_server: SIAServerTCP = SIAServerTCP(
            self._accounts, self._func, self._counts
        )

    async def async_start(self, **kwargs: Any) -> None:
        """Start the asynchronous SIA TCP server.

        The rest of the arguments are passed directly to asyncio.start_server().
        """
        _LOGGER.debug("Starting SIA.")
        coro = asyncio.start_server(
            self.sia_server.handle_line, self._host, self._port, **kwargs
        )
        self.task = asyncio.create_task(coro)

    async def async_stop(self) -> None:
        """Stop the asynchronous SIA TCP server."""
        _LOGGER.debug("Stopping SIA.")
        self.sia_server.shutdown_flag = True
        await asyncio.gather(self.task)  # type: ignore


class SIAClientUDP(SIAClient):
    """UDP Subclass."""

    protocol = CommunicationsProtocol.UDP

    def __init__(
        self,
        host: str,
        port: int,
        accounts: list[SIAAccount],
        function: Callable[[SIAEvent], Awaitable[None]],
        **kwargs: Any,
    ) -> None:
        """Create the UDP SIA Client object."""
        super().__init__(host, port, accounts, function)
        self.transport: asyncio.BaseTransport | None = None
        self.dgprotocol: asyncio.BaseProtocol | None = None

    async def async_start(self, **kwargs: Any) -> None:
        """Start the asynchronous SIA UDP server.

        The rest of the arguments are passed directly to create_datagram_endpoint().
        """
        _LOGGER.debug("Starting SIA.")
        loop = asyncio.get_running_loop()
        self.transport, self.dgprotocol = await loop.create_datagram_endpoint(
            lambda: SIAServerUDP(self._accounts, self._func, self._counts),
            local_addr=(self._host, self._port),
            **kwargs,
        )

    async def async_stop(self) -> None:
        """Stop the asynchronous SIA UDP server."""
        _LOGGER.debug("Stopping SIA.")
        if self.transport is not None:
            self.transport.close()
