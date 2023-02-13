"""This is the class for the actual TCP handler override of the handle method."""

import logging
from socketserver import BaseRequestHandler
from Crypto.Cipher import DES3
from Crypto.Random import get_random_bytes

from ..event import SIAEvent
from ..utils import ResponseType

_LOGGER = logging.getLogger(__name__)


class BaseSIAHandler(BaseRequestHandler):
    """Base case for Request handling."""

    _received_data = "".encode()
    _key = None
    _cipher = None

    def handle_raw_line(self, raw: bytes) -> None:
        """Handle the line."""
        while len(raw) > 0:
            splitter = raw.find(b"\r")
            if splitter == -1:
                line = raw
                raw = b""
            else:  # pragma: no cover
                line = raw[1:splitter]
                raw = raw[splitter + 1 :]
            decoded_line = line.decode("ascii", errors="ignore")
            event = self.server.parse_and_check_event(decoded_line)  # type: ignore
            self.respond(event)
            if event and event.response == ResponseType.ACK:
                self.server.func_wrap(event)  # type: ignore

    def respond(self, event: SIAEvent) -> None:
        """Abstract method for responding."""
        pass  # pragma: no cover


class SIATCPHandler(BaseSIAHandler):
    """Class for TCP Handling."""

    def handle(self) -> None:
        """Overwritten method for the RequestHandler."""

        if self._key is None:
            self._key = DES3.adjust_key_parity(get_random_bytes(24))
            self._cipher = DES3.new(self._key, mode=DES3.MODE_ECB)
            scrambled_key = self.OsborneHoffmanScramble(self._key)
            self.request.sendall(scrambled_key)

        while True and not self.server.shutdown_flag:  # type: ignore # pragma: no cover
            raw = self.request.recv(1024)
            if not raw:
                break

            raw = bytearray(raw)

            if self._key is not None:
                raw = self._cipher.decrypt(raw)
                padding_len = len(raw) - raw.rfind(b'\r') - 1
                raw = raw[:-padding_len]

            self.handle_raw_line(raw)

    def respond(self, event: SIAEvent) -> None:
        """Respond to the event."""
        try:
            raw = event.create_response()
            print('response', raw)

            if self._key is not None:
                block_size = 8
                padding_len = block_size-len(raw)%block_size
                padding = bytearray(chr(0)*(padding_len), 'ascii')
                raw += padding
                print(bytes(raw).hex())
                raw = self._cipher.encrypt(raw)

            self.request.sendall(raw)
        except Exception as exp:  # pragma: no cover
            _LOGGER.error(
                "Exception caught while responding to event: %s, exception: %s",
                event.create_response(),
                exp,
            )

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


class SIAUDPHandler(BaseSIAHandler):
    """Class for UDP Handling."""

    def handle(self) -> None:
        """Overwritten method for the RequestHandler."""
        if not self.server.shutdown_flag:  # type: ignore # pragma: no cover
            raw = self.request[0]
            # socket = self.request[1]
            if raw:
                raw = bytearray(raw)
                self.handle_raw_line(raw)

    def respond(self, event: SIAEvent) -> None:
        """Respond to the event."""
        try:
            self.request[1].sendto(
                event.create_response(),
                self.client_address,
            )
        except Exception as exp:  # pragma: no cover
            _LOGGER.error(
                "Exception caught while responding to event: %s, exception: %s",
                event.create_response(),
                exp,
            )
