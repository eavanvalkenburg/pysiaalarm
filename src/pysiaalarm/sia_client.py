# -*- coding: utf-8 -*-
"""This is a the main class for the SIA Client."""

from typing import Callable
from binascii import hexlify, unhexlify
import socket
import threading
import logging
from Crypto import Random
from Crypto.Cipher import AES

from pysiaalarm import __version__
from pysiaalarm.sia_event import SIAEvent
from pysiaalarm.sia_tcp_handler import SIAServer, SIATCPHandler
from pysiaalarm.sia_errors import (
    InvalidAccountFormatError,
    InvalidAccountLengthError,
    InvalidKeyFormatError,
    InvalidKeyLengthError,
    PortInUseError,
)

__author__ = "E.A. van Valkenburg"
__copyright__ = "E.A. van Valkenburg"
__license__ = "mit"
__version__ = __version__

logging.getLogger(__name__)  # .addHandler(logging.NullHandler())

global_process_event = None
ending = ""


class SIAClient(threading.Thread):
    """Class for SIA Clients."""

    def __init__(
        self,
        host: str,
        port: int,
        account_id: str,
        function: Callable[[SIAEvent], None],
        key: str = None,
    ):
        """Initialize the SIA Client."""
        threading.Thread.__init__(self)
        self._encrypted = False
        self._ending = "]"
        self._account_id = account_id
        self._key = key
        self._func = function
        self._host = host
        self._port = port
        self._validate_input()
        if self._key:
            logging.debug("Hub: init: encryption is enabled.")
            self._encrypted = True
            self._key = self._key.encode("utf8")
            self._decrypter = AES.new(
                self._key, AES.MODE_CBC, unhexlify("00000000000000000000000000000000")
            )
            _encrypter = AES.new(
                self._key, AES.MODE_CBC, Random.new().read(AES.block_size)
            )
            self._ending = (
                hexlify(_encrypter.encrypt("00000000000000|]".encode("utf8")))
                .decode(encoding="UTF-8")
                .upper()
            )
        global ending
        ending = self._ending
        self.server = SIAServer((self._host, self._port), SIATCPHandler)

    def _test_port(self):
        """ Test if the port is in use."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)  # 2 Second Timeout
        result = sock.connect_ex((self._host, self._port))
        if result == 0:
            sock.close()
            return False
        else:
            sock.close()
            return True

    def _validate_input(self):
        """ Validate the input by the user."""
        port_in_use = self._test_port()
        if port_in_use:
            raise PortInUseError

        if self._key:
            try:
                int(self._key, 16)
            except ValueError:
                raise InvalidKeyFormatError
            try:
                assert len(self._key) in (16, 24, 32)
            except AssertionError:
                raise InvalidKeyLengthError

        try:
            int(self._account_id, 16)
        except ValueError:
            raise InvalidAccountFormatError
        try:
            assert 3 <= len(self._account_id) <= 16
        except AssertionError:
            raise InvalidAccountLengthError

        return True

    def start(self):
        """Start the SIA TCP Handler."""
        logging.debug("Hub: start: starting thread.")
        global global_process_event
        global_process_event = self.process_event
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()

    def stop(self):
        """Stop the SIA TCP Handler thread."""
        logging.debug("Hub: stop: stopping thread.")
        self.server.shutdown()
        self.server.server_close()
        self.server_thread.join()

    def process_event(self, event: SIAEvent):
        """Process the Event that comes from the TCP handler."""
        try:
            logging.debug(f"Hub: Process event: {event}")
            if self._encrypted:
                event = self._decrypt_string(event)
                logging.debug(f"Hub: Process event, after decrypt: {event}")
            self._func(event)
        except Exception as exc:
            logging.error(f"Hub: Process Event: {event} gave error {exc}")

    def set_alarm(self, state):
        """Set the alarm to a specified state."""

    def _decrypt_string(self, event: SIAEvent) -> SIAEvent:
        """Decrypt the encrypted event content and parse it."""
        logging.debug("Hub: Decrypt String: Original: %s", str(event.encrypted_content))
        resmsg = self._decrypter.decrypt(unhexlify(event.encrypted_content)).decode(
            encoding="UTF-8", errors="replace"
        )
        logging.debug(f"Hub: Decrypt String: Decrypted: {resmsg}")
        event.parse_decrypted(resmsg)
        return event
