"""This is the class for the actual TCP handler override of the handle method."""
import asyncio
import logging
from typing import Callable, Coroutine, Dict, Union

from .. import __author__, __copyright__, __license__, __version__
from ..base_sia_server import BaseSIAServer
from ..sia_account import SIAAccount, SIAResponseType
from ..sia_event import SIAEvent

_LOGGER = logging.getLogger(__name__)
empty_bytes = b""


class SIAServer(BaseSIAServer):
    """Class for SIA Server Async."""

    def __init__(
        self,
        accounts: Dict[str, SIAAccount],
        func: Callable[[SIAEvent], None],
        counts: Dict,
    ):
        """Create a SIA Server.

        Arguments:
            server_address {tuple(string, int)} -- the address the server should listen on.
            accounts Dict[str, SIAAccount] -- accounts as dict with account_id as key, SIAAccount object as value.
            func Callable[[SIAEvent], None] -- Function called for each valid SIA event, that can be matched to a account.
            error_count Dict -- counter kept by client to give insights in how many errorous events were discarded of each type.

        """
        BaseSIAServer.__init__(self, accounts, func, counts)

    async def handle_line(self, reader, writer):
        """Handle for SIA Events.

        Arguments:
            reader {asyncio.StreamReader} -- StreamReader with new data.
            writer {asyncio.StreamWriter} -- StreamWriter to respond.

        """
        while True and not self.shutdown_flag:
            try:
                data = await reader.read(1000)
            except ConnectionResetError:
                break
            if data == empty_bytes or reader.at_eof():
                break
            line = str.strip(data.decode("ascii"))
            if not line:
                return
            _LOGGER.debug("Incoming line: %s", line)
            self.counts["events"] = self.counts["events"] + 1
            event, account, response = self.parse_and_check_event(line)
            writer.write(account.create_response(event, response))
            await writer.drain()

            if not (event and response == SIAResponseType.ACK):
                continue
            self.counts["valid_events"] = self.counts["valid_events"] + 1
            try:
                await self.func(event)
            except Exception as exp:
                _LOGGER.warning(
                    "Last event: %s, gave error in user function: %s.", event, exp
                )
                self.counts["errors"]["user_code"] = (
                    self.counts["errors"]["user_code"] + 1
                )

        writer.close()
