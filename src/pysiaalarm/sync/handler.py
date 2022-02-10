"""This is the class for the actual TCP handler override of the handle method."""
from __future__ import annotations

import logging
from abc import abstractmethod
from socketserver import BaseRequestHandler

from ..event import SIAEvent

_LOGGER = logging.getLogger(__name__)


class BaseSIAHandler(BaseRequestHandler):
    """Base case for Request handling."""

    _received_data = "".encode()

    def handle_raw_line(self, raw: bytes) -> None:
        """Handle the line."""
        while len(raw) > 0:
            splitter = raw.find(b"\r")
            if splitter == -1:
                data = raw
                raw = b""
            else:  # pragma: no cover
                data = raw[1:splitter]
                raw = raw[splitter + 1 :]
            # decoded_line = line.decode("ascii", errors="ignore")
            event = self.server.parse_and_check_event(data)  # type: ignore
            self.respond(event)
            self.server.func_wrap(event)  # type: ignore

    @abstractmethod
    def respond(self, event: SIAEvent) -> None:
        """Abstract method for responding."""


class SIATCPHandler(BaseSIAHandler):
    """Class for TCP Handling."""

    def handle(self) -> None:
        """Overwritten method for the RequestHandler."""
        while True and not self.server.shutdown_flag:  # type: ignore # pragma: no cover
            raw = self.request.recv(1024)
            if not raw:
                break
            raw = bytearray(raw)
            self.handle_raw_line(raw)

    def respond(self, event: SIAEvent) -> None:
        """Respond to the event."""
        try:
            self.request.sendall(event.create_response())
        except Exception as exp:  # pragma: no cover # pylint: disable=broad-except
            _LOGGER.error(
                "Exception caught while responding to event: %s, exception: %s",
                event.create_response(),
                exp,
            )


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
        except Exception as exp:  # pragma: no cover # pylint: disable=broad-except
            _LOGGER.error(
                "Exception caught while responding to event: %s, exception: %s",
                event.create_response(),
                exp,
            )
