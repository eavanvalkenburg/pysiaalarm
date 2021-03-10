#!/usr/bin/python
"""Run a test client."""
import json
import logging
import random
import socket
import sys
import time

from Crypto import Random
from Crypto.Cipher import AES

from pysiaalarm.base_sia_client import Protocol
from .test_utils import create_line_from_test_case, create_random_line

logging.basicConfig(level=logging.INFO)
_LOGGER = logging.getLogger(__name__)


def send_messages(config, test_case=None, time_between=5, protocol=Protocol.TCP):
    """Create the socket client and start sending messages every 5 seconds, until stopped, or the server disappears."""
    _LOGGER.info("Test client config: %s", config)
    host = config["host"]  # as both code is running on same pc
    port = config["port"]  # socket server port number
    # socket.SOCK_DGRAM
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM if protocol == Protocol.TCP else socket.SOCK_DGRAM) as sock:
        try:
            sock.connect((host, port))  # connect to the server
        except ConnectionRefusedError:
            _LOGGER.error("Connection refused in test_alarm.py.")
            return

        _LOGGER.info("Number of cases: %s", len(test_case))
        if test_case:
            for tc in test_case:
                message = create_line_from_test_case(config, tc)
                _LOGGER.debug(f"Sending to server: {message}")
                sock.sendall(message.encode())  # send message
                data = sock.recv(1024).decode()  # receive response
                time.sleep(time_between)
            return
        while True:
            message = create_random_line(config)
            _LOGGER.debug(f"Sending to server: {message}")
            sock.sendall(message.encode())  # send message
            data = sock.recv(1024).decode()  # receive response
            _LOGGER.debug(f"Received from server: {data}")  # show in terminal
            time.sleep(time_between)


if __name__ == "__main__":
    """Run main with a config."""
    _LOGGER.info(sys.argv)
    if sys.argv[1]:
        file = sys.argv[1]
    else:
        file = "unencrypted_config.json"
    with open(file, "r") as f:
        config = json.load(f)
    send_messages(config)
