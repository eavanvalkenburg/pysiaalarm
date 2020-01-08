# -*- coding: utf-8 -*-
"""
This is a the main class for the SIA Client.
"""

from typing import Callable, Any
from binascii import hexlify, unhexlify
import socketserver
import threading
import argparse
import sys
import logging
from Crypto import Random
from Crypto.Cipher import AES
import requests
from requests_toolbelt.utils import dump
import sseclient

from pysia import __version__
from .sia_event import SIAEvent
from .sia_tcp_handler import SIATCPHandler

__author__ = "E.A. van Valkenburg"
__copyright__ = "E.A. van Valkenburg"
__license__ = "mit"

_LOGGER = logging.getLogger(__name__)

class SIAClient(threading.Thread):
    """Class for SIA Clients."""

    def __init__(self, host: str, port: int, account_id: str, key: str, function: Callable[[SIAEvent], None]):
        """Initialize the SIA Client."""
        threading.Thread.__init__(self)
        self._encrypted = False
        self._account_id = account_id
        self._key = key
        self._func = function
        self._host = host
        self._port = port
        if self._key:
            _LOGGER.debug("Hub: init: encryption is enabled.")
            self._encrypted = True
            self._key = self._key.encode("utf8")
            # IV standards from https://manualzz.com/doc/11555754/sia-digital-communication-standard-%E2%80%93-internet-protocol-ev...
            # page 12 specifies the decrytion IV to all zeros.
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

        socketserver.TCPServer.allow_reuse_address = True
        self.server = socketserver.TCPServer((self._host, self._port), SIATCPHandler)

    def start(self):
        """Start the SIA TCP Handler."""
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()

    def stop(self):
        """Stop the SIA TCP Handler thread."""
        self.server.shutdown()
        self.server.server_close()

    def process_event(self, event: SIAEvent) -> str:
        """Process the Event that comes from the TCP handler."""
        try:
            _LOGGER.debug("Hub: Process event: %s", event)
            if self._encrypted:
                event = self._decrypt_string(event)
                _LOGGER.debug("Hub: Process event, after decrypt: %s", event)
            self._func(event)
        except Exception as exc:
            _LOGGER.error("Hub: Process Event: %s gave error %s", event, str(exc))

        # Even if decrypting or something else gives an error, create the acknowledgement message.
        return '"ACK"{}L0#{}[{}'.format(event.sequence, self._account_id, self._ending)

    def _decrypt_string(self, event: SIAEvent) -> SIAEvent:
        """Decrypt the encrypted event content and parse it."""
        _LOGGER.debug("Hub: Decrypt String: Original: %s", str(event.encrypted_content))
        resmsg = self._decrypter.decrypt(unhexlify(event.encrypted_content)).decode(
            encoding="UTF-8", errors="replace"
        )
        _LOGGER.debug("Hub: Decrypt String: Decrypted: %s", resmsg)
        event.parse_decrypted(resmsg)
        return event