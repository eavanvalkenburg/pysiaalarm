# -*- coding: utf-8 -*-
"""This is the class for the actual TCP handler override of the handle method."""

from datetime import datetime
import time
from socketserver import ThreadingTCPServer, BaseRequestHandler
import logging
from pysiaalarm.sia_event import SIAEvent
from pysiaalarm import sia_client
from pysiaalarm.sia_errors import CRCMismatchError, ReceivedAccountUnknownError

logging.getLogger(__name__)


class SIAServer(ThreadingTCPServer):
    """Class for a SIA Server."""

    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, server_address, RequestHandlerClass):
        """Create a SIA Server.

        Arguments:
            server_address {tuple(string, int)} -- the address the server should listen on.
            RequestHandlerClass {[type]} -- RequestHandlerClass, should be SIATCPHandler.

        """
        self.request_handler = RequestHandlerClass
        ThreadingTCPServer.__init__(self, server_address, self.request_handler)

    def handle_error(self, request, client_address):
        logging.error("Last request %s coming from %s gave an error.", request, client_address)

class SIATCPHandler(BaseRequestHandler):
    """Class for the TCP Handler."""

    _received_data = "".encode()

    def handle_line(self, line: str):
        """Handle a line coming in on the server.

        Arguments:
            line {str} -- The line after initial handling.

        Raises:
            CRCMismatchError: Error is the CRC does not match.

        """
        logging.debug(f"Income raw string: {line}")
        try:
            event = SIAEvent(line)
            account = sia_client.GLOB_ACCOUNTS.get(event.account)
            if account:
                event = account._decrypt_string(event)
                if not event.valid_message:
                    raise CRCMismatchError("CRC mismatch in event, received: %s, calculated: %s", event.msg_crc, event.calc_crc)
                response = f'"ACK"{event.sequence}L0#{event.account}[{account.ending}'
            else:
                raise ReceivedAccountUnknownError("Unknown or non-existing account was used by the event: &s", event)
        except Exception as exc:
            logging.error("Error: %s", exc)
            timestamp = datetime.fromtimestamp(time.time()).strftime(
                "_%H:%M:%S,%m-%d-%Y"
            )
            response = f'"NAK"0000L0R0A0[]{timestamp}'
            # if the line could not be parsed, no account is known or the crc does not match, the event is invalid and ignored, security risk otherwise.
            event = None

        header = ("%04x" % len(response)).upper()

        res = f"\n{SIAEvent.crc_calc(response)}{header}{response}\r"
        byte_response = str.encode(res)
        self.request.sendall(byte_response)

        # finally run the event process code if the event is valid.
        if event:
            sia_client.GLOB_PROCESS_EVENT(event=event)

    def handle(self):
        """Overwritten method for the RequestHandler."""
        line = b""
        while True:
            raw = self.request.recv(1024)
            if not raw:
                return
            raw = bytearray(raw)
            while True:
                splitter = raw.find(b"\r")
                if splitter > -1:
                    line = raw[1:splitter]
                    raw = raw[splitter + 1:]
                else:
                    break
                self.handle_line(line.decode())
            if sia_client.GLOB_STOP_THREADS:
                break


    # @staticmethod
    # def crc_calc(msg: str) -> str:
    #     """Calculate the CRC of a message.

    #     Arguments:
    #         msg {str} -- The message for which the CRC needs to be calculated.

    #     Returns:
    #         str -- the calculated CRC value.

    #     """
    #     new_crc = 0
    #     for letter in msg:
    #         temp = ord(letter)
    #         for _ in range(0, 8):
    #             temp ^= new_crc & 1
    #             new_crc >>= 1
    #             if (temp & 1) != 0:
    #                 new_crc ^= 0xA001
    #             temp >>= 1

    #     return ("%x" % new_crc).upper().zfill(4)
