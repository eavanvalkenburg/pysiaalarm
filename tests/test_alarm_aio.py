#!/usr/bin/python
"""Run a test client."""
import asyncio
import json
import logging
import sys

from .test_utils import create_line_from_test_case, create_random_line


logging.basicConfig(level=logging.DEBUG)
_LOGGER = logging.getLogger(__name__)


async def async_send_messages(config, test_case, time_between):
    """Send message async."""
    host = config["host"]
    port = config["port"]
    _LOGGER.debug("Opening connection")
    reader, writer = await asyncio.open_connection(host, port)
    if test_case:
        _LOGGER.debug("Number of cases: %s", len(test_case))
        for tc in test_case:
            message = create_line_from_test_case(config, tc)
            _LOGGER.debug("Message: %s", message)
            writer.write(message.encode())
            data = await reader.read(100)
            _LOGGER.debug(f"Received from server: {data.decode()}")
            await asyncio.sleep(time_between)
        writer.close()
        return
    try:
        while True:
            message = create_random_line(config)
            _LOGGER.debug("Message: %s", message)
            writer.write(message.encode())
            data = await reader.read(100)
            _LOGGER.debug(f"Received from server: {data.decode()}")
            await asyncio.sleep(time_between)
    finally:
        writer.close()


if __name__ == "__main__":
    """Run main with a config."""
    _LOGGER.info(sys.argv)
    try:  # sys.argv.index(1)
        file = sys.argv[1]
    except:
        file = "tests//local_config.json"
    with open(file, "r") as f:
        config = json.load(f)
    asyncio.get_event_loop().run_until_complete(async_send_messages(config, None, 3))
