"""This is the class for the actual TCP handler override of the handle method."""
from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from .. import __author__, __copyright__, __license__, __version__
from ..account import SIAAccount
from ..base_server import BaseSIAServer
from ..const import EMPTY_BYTES
from ..event import SIAEvent
from ..utils import Counter

_LOGGER = logging.getLogger(__name__)


class SIAServerTCP(BaseSIAServer):
    """Class for SIA TCP Server Async."""

    def __init__(
        self,
        accounts: dict[str, SIAAccount],
        func: Callable[[SIAEvent], Awaitable[None]],
        counts: Counter,
    ):
        """Create a SIA TCP Server.

        Arguments:
            accounts Dict[str, SIAAccount] -- accounts as dict with account_id as key, SIAAccount object as value.  # pylint: disable=line-too-long
            func Callable[[SIAEvent], None] -- Function called for each valid SIA event, that can be matched to a account.  # pylint: disable=line-too-long
            counts Counter -- counter kept by client to give insights in how many errorous events were discarded of each type.  # pylint: disable=line-too-long
        """
        BaseSIAServer.__init__(self, accounts, counts, async_func=func)

    async def handle_line(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """Handle line for SIA Events. This supports TCP connections.

        Arguments:
            reader {asyncio.StreamReader} -- StreamReader with new data.
            writer {asyncio.StreamWriter} -- StreamWriter to respond.

        """
        try:
            while not self.shutdown_flag:  # pragma: no cover  # type: ignore
                try:
                    data = await reader.read(1000)
                except ConnectionResetError:
                    break
                if data == EMPTY_BYTES or reader.at_eof():
                    break
                event = self.parse_and_check_event(data)
                if not event:
                    continue
                _LOGGER.debug("Incoming event: %s", event)
                response = event.create_response()
                _LOGGER.debug("Outgoing line: %s", response)
                writer.write(response)
                await writer.drain()
                await self.async_func_wrap(event)
        finally:
            writer.close()
            await writer.wait_closed()


class SIAServerUDP(BaseSIAServer, asyncio.DatagramProtocol):
    """Class for SIA UDP Server Async."""

    def __init__(
        self,
        accounts: dict[str, SIAAccount],
        func: Callable[[SIAEvent], Awaitable[None]],
        counts: Counter,
    ):
        """Create a SIA UDP Server.

        Arguments:
            server_address {tuple(string, int)} -- the address the server should listen on.
            accounts {Dict[str, SIAAccount]} -- accounts as dict with account_id as key, SIAAccount object as value.  # pylint: disable=line-too-long
            func {Callable[[SIAEvent], None]} -- Function called for each valid SIA event, that can be matched to a account.  # pylint: disable=line-too-long
            counts {Counter} -- counter kept by client to give insights in how many errorous events were discarded of each type.  # pylint: disable=line-too-long
        """
        BaseSIAServer.__init__(self, accounts, counts, async_func=func)
        self.transport: asyncio.DatagramTransport | None = None

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        """Connect callback for datagrams."""
        assert isinstance(transport, asyncio.DatagramTransport)
        self.transport = transport

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        """Receive and process datagrams. This support UDP connections."""
        if self.shutdown_flag:  # type: ignore
            return
        event = self.parse_and_check_event(data)
        if not event:
            return
        if self.transport is not None:
            self.transport.sendto(event.create_response(), addr)
        asyncio.create_task(self.async_func_wrap(event))

    def connection_lost(self, _: Any) -> None:
        """Close and reset transport when connection lost."""
        if self.transport:
            self.transport.close()
