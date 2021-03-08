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

from .test_utils import create_line

logging.basicConfig(level=logging.INFO)
_LOGGER = logging.getLogger(__name__)


def send_messages(
    config,
    test_case=None,
    time_between=5,
):
    """Create the socket client and start sending messages every 5 seconds, until stopped, or the server disappears."""
    _LOGGER.info("Test client config: %s", config)
    host = config["host"]  # as both code is running on same pc
    port = config["port"]  # socket server port number

    client_socket = socket.socket()  # instantiate
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        client_socket.connect((host, port))  # connect to the server
    except ConnectionRefusedError:
        _LOGGER.error("Connection refused in test_client.py.")
        return

    _LOGGER.info("Number of cases: %s", len(test_case))
    if test_case:
        for tc in test_case:
            message = create_line(config, tc)
            _LOGGER.debug(f"Sending to server: {message}")
            client_socket.send(message.encode())  # send message
            data = client_socket.recv(1024).decode()  # receive response
            time.sleep(time_between)
        client_socket.close()  # close the connection
        return
    try:
        while True:
            message = create_line(config, None)
            _LOGGER.debug(f"Sending to server: {message}")
            client_socket.send(message.encode())  # send message
            data = client_socket.recv(1024).decode()  # receive response
            _LOGGER.debug(f"Received from server: {data}")  # show in terminal
            time.sleep(time_between)
    finally:
        client_socket.close()  # close the connection


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
