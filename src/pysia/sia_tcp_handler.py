# -*- coding: utf-8 -*-
"""This is the class for the actual TCP handler override of the handle method."""

from datetime import datetime
import time
import socketserver
import logging
from pysia.sia_event import SIAEvent
from pysia import sia_client

logging.getLogger(__name__)


class SIAServer(socketserver.TCPServer):  # socketserver.ThreadingMixIn,
    """Class for a SIA Server."""

    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, server_address, RequestHandlerClass):
        """Initialize the server."""
        self.request_handler = RequestHandlerClass
        socketserver.TCPServer.__init__(self, server_address, self.request_handler)


class SIATCPHandler(socketserver.BaseRequestHandler):
    """Class for the TCP Handler."""

    _received_data = "".encode()

    def handle_line(self, line: str):
        """Handle the line in detail and call event processing code."""
        logging.debug(f"TCP: Handle Line: Income raw string: {line}")
        print(f"Handle line: {line}")
        # parse the event
        try:
            event = SIAEvent(line)
            logging.debug(f"TCP: Handle Line: event: {event}")
            if not event.valid_message:
                logging.error(
                    f"TCP: Handle Line: CRC mismatch, received: {event.msg_crc}, calculated: {event.calc_crc}"
                )
                raise Exception("CRC mismatch in event, check the logs.")
            response = f'"ACK"{event.sequence}L0#{event.account}[{sia_client.ending}'
        except Exception as exc:
            logging.error(f"TCP: Handle Line: error: {exc}")
            timestamp = datetime.fromtimestamp(time.time()).strftime(
                "_%H:%M:%S,%m-%d-%Y"
            )
            response = f'"NAK"0000L0R0A0[]{timestamp}'
            # if the line could not be parsed or the crc does not match, the event is invalid and ignored, security risk otherwise.
            event = None

        # send the response.
        try:
            logging.debug(f"TCP: Handle Line: response: {response}")
            header = ("%04x" % len(response)).upper()
            res = f"\n{SIATCPHandler.crc_calc(response)}{header}{response}\r"
            byte_response = str.encode(res)
            self.request.sendall(byte_response)
        except Exception as exp:
            logging.info(f"Could not send response, error: {exp}")

        # finally run the event process code if the event is valid.
        if event:
            sia_client.global_process_event(event=event)

    def handle(self):
        """Overridden method for handle lines."""
        line = b""
        try:
            while True:
                raw = self.request.recv(1024)
                print(f"Raw: {raw}")
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
                    print(f"Line handle: {line.decode()}")
                    self.handle_line(line.decode())
        except Exception as exc:
            logging.error(f"TCP: Handle: last line {line.decode()} gave error: {exc}")
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
