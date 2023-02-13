"""This is the class for the actual TCP handler override of the handle method."""
import asyncio
import logging
from typing import Any, Callable, Dict, Optional, Tuple, Union
from Crypto.Cipher import DES3
from Crypto.Random import get_random_bytes

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
        key: bytes = None,
        cipher = None 
    ) -> None:
        """Respond to the message using the right approach."""
        try:
            if writer:

                raw = event.create_response()

                block_size = 8
                padding_len = block_size-len(raw)%block_size
                padding = bytearray(chr(0)*(padding_len), 'ascii')
                raw += padding
                raw = cipher.encrypt(raw)

                writer.write(raw)
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
        key: bytes = None,
        cipher = None 
    ) -> None:
        """Handle data universally for both TCP and UDP."""
        line = str.strip(data.decode("ascii", errors="ignore"))
        if not line:  # pragma: no cover
            return
        event = self.parse_and_check_event(line)  # type: ignore
        await self._respond(event, writer=writer, addr=addr, key=key, cipher=cipher)
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

        key = DES3.adjust_key_parity(get_random_bytes(24))
        cipher = DES3.new(key, mode=DES3.MODE_ECB)
        scrambled_key = self.OsborneHoffmanScramble(key)
        writer.write(scrambled_key)
        await writer.drain()

        while True and not self.shutdown_flag:  # pragma: no cover  # type: ignore
            try:
                data = await reader.read(1000)
            except ConnectionResetError:
                break
            if data == EMPTY_BYTES or reader.at_eof():
                break

            data = cipher.decrypt(data)
            padding_len = len(data) - data.rfind(b'\r') - 1
            data = data[:-padding_len]

            await self._handle_data(data, writer=writer, key=key, cipher=cipher)

        writer.close()

    def OsborneHoffmanScramble(self, input):
        key = bytearray(input)
        key[3] ^= 0x05
        key[4] ^= 0x23
        key[9] ^= 0x29
        key[1] ^= 0x2D
        key[6] ^= 0x39
        key[20] ^= 0x44
        key[8] ^= 0x45
        key[16] ^= 0x45
        key[5] ^= 0x49
        key[18] ^= 0x50
        key[23] ^= 0x54
        key[0] ^= 0x55
        key[22] ^= 0x69
        key[2] ^= 0x6A
        key[15] ^= 0x88
        key[19] ^= 0x8A
        key[12] ^= 0x94
        key[17] ^= 0xA3
        key[7] ^= 0xA8
        key[21] ^= 0xAA
        key[14] ^= 0xB5
        key[13] ^= 0xC2
        key[10] ^= 0xD3
        key[11] ^= 0xE9
        return key

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        """Connect callback for datagrams."""
        self.transport = transport

    def datagram_received(self, data: bytes, addr: Tuple[str, int]) -> None:
        """Receive and process datagrams. This support UDP connections."""
        asyncio.create_task(self._handle_data(data, addr=addr))

    def connection_lost(self, _: Any) -> None:
        """Close and reset transport when connection lost."""
        self.transport.close()
