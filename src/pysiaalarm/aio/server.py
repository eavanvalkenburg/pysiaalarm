"""This is the class for the actual TCP handler override of the handle method."""
import asyncio
import logging
from typing import Any, Callable, Dict, Optional, Tuple, Union

from .. import __author__, __copyright__, __license__, __version__
from ..account import SIAAccount
from ..base_server import BaseSIAServer
from ..const import EMPTY_BYTES
from ..event import NAKEvent, OHEvent, SIAEvent
from ..utils import Counter, ResponseType

_LOGGER = logging.getLogger(__name__)


class SIAServer(BaseSIAServer, asyncio.DatagramProtocol):
    """Class for SIA TCP Server Async."""

    def __init__(
        self,
        accounts: Dict[str, SIAAccount],
        func: Callable[[SIAEvent], None],
        counts: Counter,
    ):
        """Create a SIA Server.

        Arguments:
            server_address {tuple(string, int)} -- the address the server should listen on.
            accounts {Dict[str, SIAAccount]} -- accounts as dict with account_id as key, SIAAccount object as value.
            func {Callable[[SIAEvent], None]} -- Function called for each valid SIA event, that can be matched to a account.
            counts {Counter} -- counter kept by client to give insights in how many errorous events were discarded of each type.

        """
        BaseSIAServer.__init__(self, accounts, func, counts)

    async def _respond(
        self,
        event: Union[SIAEvent, OHEvent, NAKEvent],
        writer: asyncio.StreamWriter = None,
        addr: Optional[Tuple[str, int]] = None,
    ) -> None:
        """Respond to the message using the right approach."""
        try:
            if writer:
                writer.write(event.create_response())
                await writer.drain()
                return
            if (
                self.transport
                and addr
                and isinstance(self.transport, asyncio.DatagramTransport)
            ):  # pragma: no cover
                self.transport.sendto(event.create_response(), addr)
                return
        except Exception as exp:  # pragma: no cover
            _LOGGER.error(
                "Exception caught while responding with: %s, exception: %s",
                event.create_response(),
                exp,
            )

    async def _handle_data(
        self,
        data: bytes,
        writer: asyncio.StreamWriter = None,
        addr: Optional[Tuple[str, int]] = None,
    ) -> None:
        """Handle data universally for both TCP and UDP."""
        line = str.strip(data.decode("ascii", errors="ignore"))
        if not line:  # pragma: no cover
            return
        event = self.parse_and_check_event(line)  # type: ignore
        await self._respond(event, writer=writer, addr=addr)
        if event and isinstance(event, SIAEvent) and event.response == ResponseType.ACK:
            await self.async_func_wrap(event)  # type: ignore

    async def handle_line(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """Handle line for SIA Events. This supports TCP connections.

        Arguments:
            reader {asyncio.StreamReader} -- StreamReader with new data.
            writer {asyncio.StreamWriter} -- StreamWriter to respond.

        """
        while True and not self.shutdown_flag:  # pragma: no cover  # type: ignore
            try:
                data = await reader.read(1000)
            except ConnectionResetError:
                break
            if data == EMPTY_BYTES or reader.at_eof():
                break
            await self._handle_data(data, writer=writer)

        writer.close()

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        """Connect callback for datagrams."""
        self.transport = transport

    def datagram_received(self, data: bytes, addr: Tuple[str, int]) -> None:
        """Receive and process datagrams. This support UDP connections."""
        asyncio.create_task(self._handle_data(data, addr=addr))

    def connection_lost(self, _: Any) -> None:
        """Close and reset transport when connection lost."""
        self.transport.close()
