#!/usr/bin/python
"""Run a test client."""
import json
import logging
import socket
import sys
import time

from pysiaalarm import CommunicationsProtocol
from .test_utils import create_line_from_test_case, create_random_line

logging.basicConfig(level=logging.DEBUG)
_LOGGER = logging.getLogger(__name__)


def send_messages(config, test_case=None, time_between=5):
    """Create the socket client and start sending messages every 5 seconds, until stopped, or the server disappears."""
    _LOGGER.info("Test client config: %s", config)
    host = config["host"]
    port = config["port"]
    protocol = (
        socket.SOCK_STREAM
        if config["protocol"] == CommunicationsProtocol.TCP
        else socket.SOCK_DGRAM
    )

    with socket.socket(socket.AF_INET, protocol) as sock:
        try:
            sock.connect((host, port))  # connect to the server
        except ConnectionRefusedError:
            _LOGGER.error("Connection refused in test_alarm.py.")
            return

        if test_case:
            message = create_line_from_test_case(config, test_case)
            _LOGGER.debug(f"Sending to server: {message}")
            sock.sendall(message.encode())  # send message
            data = sock.recv(1024).decode()  # receive response
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
    try:  # sys.argv.index(1)
        file = sys.argv[1]
    except:
        file = "tests//local_config.json"
    with open(file, "r") as f:
        config = json.load(f)
    send_messages(config)
