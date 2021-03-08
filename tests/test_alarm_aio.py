#!/usr/bin/python
"""Run a test client."""
import asyncio
import json
import logging
import sys

from .test_utils import create_line


logging.basicConfig(level=logging.INFO)
_LOGGER = logging.getLogger(__name__)


async def async_tcp_sender(message, host, port):
    """Create TCP client."""
    _LOGGER.debug(f"Trying to send: {message}")

    reader, writer = await asyncio.open_connection(host, port, reuse_address=True)
    writer.write(message.encode())
    data = await reader.read(100)
    _LOGGER.debug(f"Received from server: {data.decode()}")
    writer.close()


async def async_send_messages(config, test_case, time_between):
    """Send message async."""
    host = config["host"]
    port = config["port"]
    if test_case:
        _LOGGER.debug("Number of cases: %s", len(test_case))
        for tc in test_case:
            message = create_line(config, tc)
            _LOGGER.debug("Message: %s", message)
            await async_tcp_sender(message, host, port)
            await asyncio.sleep(time_between)
        return

    while True:
        message = create_line(config, None)
        _LOGGER.debug("Message: %s", message)
        await async_tcp_sender(message, host, port)
        await asyncio.sleep(time_between)


if __name__ == "__main__":
    """Run main with a config."""
    _LOGGER.info(sys.argv)
    if sys.argv and sys.argv[1]:
        file = sys.argv[1]
    else:
        file = "tests/encrypted_config.json"
    with open(file, "r") as f:
        config = json.load(f)
    asyncio.get_event_loop().run_until_complete(async_send_messages(config, None, 3))
