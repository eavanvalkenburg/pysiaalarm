# -*- coding: utf-8 -*-
"""
This is the class for the actual TCP handler override of the handle method.
"""

import socketserver
import argparse
import sys
import logging
from Crypto import Random
from Crypto.Cipher import AES
import requests
from requests_toolbelt.utils import dump
import sseclient
# from .sia_client import SIAClient

_LOGGER = logging.getLogger(__name__)

class SIATCPHandler(socketserver.BaseRequestHandler):
    """Class for the TCP Handler."""

    _received_data = "".encode()

    def handle_line(self, line: str):
        """Method called for each line that comes in."""
        _LOGGER.debug("TCP: Handle Line: Income raw string: %s", line)
        self.SIAClient = SIAClient
        try:
            event = SIAEvent(line)
            _LOGGER.debug("TCP: Handle Line: event: %s", str(event))
            if not event.valid_message:
                _LOGGER.error(
                    "TCP: Handle Line: CRC mismatch, received: %s, calculated: %s",
                    event.msg_crc,
                    event.calc_crc,
                )
                raise Exception("CRC mismatch")
            # TODO callback to Client
            response = self.SIAClient.process_event(event)
        except Exception as exc:
            _LOGGER.error("TCP: Handle Line: error: %s", str(exc))
            timestamp = datetime.fromtimestamp(time.time()).strftime(
                "_%H:%M:%S,%m-%d-%Y"
            )
            response = '"NAK"0000L0R0A0[]' + timestamp

        header = ("%04x" % len(response)).upper()
        response = "\n{}{}{}\r".format(
            SIATCPHandler.crc_calc(response), header, response
        )
        byte_response = str.encode(response)
        self.request.sendall(byte_response)

    def handle(self):
        """Method called for handling."""
        line = b""
        try:
            while True:
                raw = self.request.recv(1024)
                if not raw:
                    return
                raw = bytearray(raw)
                while True:
                    splitter = raw.find(b"\r")
                    if splitter > -1:
                        line = raw[1:splitter]
                        raw = raw[splitter + 1 :]
                    else:
                        break

                    self.handle_line(line.decode())
        except Exception as exc:
            _LOGGER.error(
                "TCP: Handle: last line %s gave error: %s", line.decode(), str(exc)
            )
            return

    @staticmethod
    def crc_calc(msg: str) -> str:
        """Calculate the CRC of the response."""
        new_crc = 0
        for letter in msg:
            temp = ord(letter)
            for _ in range(0, 8):
                temp ^= new_crc & 1
                new_crc >>= 1
                if (temp & 1) != 0:
                    new_crc ^= 0xA001
                temp >>= 1

        return ("%x" % new_crc).upper().zfill(4)
