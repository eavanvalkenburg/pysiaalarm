"""This is the class for the actual TCP handler override of the handle method."""
import asyncio
import logging
from typing import Callable, Dict

from pysiaalarm.sia_const import Protocol

from .. import __author__, __copyright__, __license__, __version__
from ..base_sia_server import BaseSIAServer
from ..sia_account import SIAAccount, SIAResponseType
from ..sia_event import SIAEvent

_LOGGER = logging.getLogger(__name__)
empty_bytes = b""


class SIAServer(BaseSIAServer):
    """Class for SIA TCP Server Async."""

    def __init__(
        self,
        accounts: Dict[str, SIAAccount],
        func: Callable[[SIAEvent], None],
        counts: Dict,
        protocol: Protocol = Protocol.TCP,
    ):
        """Create a SIA Server.

        Arguments:
            server_address {tuple(string, int)} -- the address the server should listen on.
            accounts {Dict[str, SIAAccount]} -- accounts as dict with account_id as key, SIAAccount object as value.
            func {Callable[[SIAEvent], None]} -- Function called for each valid SIA event, that can be matched to a account.
            error_count {Dict} -- counter kept by client to give insights in how many errorous events were discarded of each type.
            protocol {Protocol Enum} -- Protocol to use, TCP or UDP.

        """
        BaseSIAServer.__init__(self, accounts, func, counts, protocol)

    async def _respond(self, event, account, resp_type, writer=None, addr=None):
        """Respond to the message using the right approach."""
        response = (
            account.create_response(event, resp_type)
            if account
            else SIAAccount.create_accountless_response(resp_type)
        )
        try:
            if writer:
                writer.write(response)
                await writer.drain()
                return
        except Exception as exp:
            _LOGGER.error(
                "Exception caught while responding to event: %s, exception: %s",
                event,
                exp,
            )
        try:
            if self.transport and addr:
                self.transport.sendto(response, addr)
                return
        except Exception as exp:
            _LOGGER.error(
                "Exception caught while responding to event: %s, exception: %s",
                event,
                exp,
            )

        _LOGGER.warning(
            "If both writer and transport are empty there is no way to respond!"
        )

    async def _handle_data(self, data, reader=None, writer=None, addr=None):
        """Handle data universally for both TCP and UDP."""
        line = str.strip(data.decode("ascii", errors="ignore"))
        if not line:
            return
        _LOGGER.debug("Incoming line: %s", line)
        self.counts["events"] = self.counts["events"] + 1

        event, account, resp_type = self.parse_and_check_event(line)

        await self._respond(event, account, resp_type, writer=writer, addr=addr)
        if event and resp_type == SIAResponseType.ACK:
            await self.async_func_wrap(event)

    async def handle_line(self, reader, writer):
        """Handle line for SIA Events. This supports TCP connections.

        Arguments:
            reader {asyncio.StreamReader} -- StreamReader with new data.
            writer {asyncio.StreamWriter} -- StreamWriter to respond.

        """
        while True and not self.shutdown_flag:
            try:
                data = await reader.read(1000)
            except ConnectionResetError:
                break
            if data == empty_bytes or reader.at_eof():
                break
            await self._handle_data(data, reader=reader, writer=writer)

        writer.close()

    def connection_made(self, transport) -> None:
        """Connect callback for datagrams."""
        self.transport = transport

    def datagram_received(self, data, addr):
        """Receive and process datagrams. This support UDP connections."""
        asyncio.create_task(self._handle_data(data, addr=addr))

    def connection_lost(self):
        """Close and reset transport when connection lost."""
        self.transport.close()
