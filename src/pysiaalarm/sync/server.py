"""This is the class for the actual TCP handler override of the handle method."""
from __future__ import annotations

import logging
from collections.abc import Callable
from socketserver import ThreadingTCPServer, ThreadingUDPServer

from ..account import SIAAccount
from ..base_server import BaseSIAServer
from ..event import SIAEvent
from ..utils import Counter
from .handler import SIATCPHandler, SIAUDPHandler

_LOGGER = logging.getLogger(__name__)


class SIATCPServer(ThreadingTCPServer, BaseSIAServer):
    """Class for a threaded SIA TCP Server."""

    daemon_threads = True
    allow_reuse_address = True

    def __init__(
        self,
        server_address: tuple[str, int],
        accounts: dict[str, SIAAccount],
        func: Callable[[SIAEvent], None],
        counts: Counter,
    ):
        """Create a SIA TCP Server.

        Arguments:
            server_address Tuple[string, int] -- the address the server should listen on.
            accounts Dict[str, SIAAccount] -- accounts as dict with account_id as key, SIAAccount object as value.  # pylint: disable=line-too-long
            func Callable[[SIAEvent], None] -- Function called for each valid SIA event, that can be matched to a account.  # pylint: disable=line-too-long
            counts Counter -- counter kept by client to give insights in how many errorous events were discarded of each type.  # pylint: disable=line-too-long
        """
        ThreadingTCPServer.__init__(self, server_address, SIATCPHandler)
        BaseSIAServer.__init__(self, accounts, counts, func=func)


class SIAUDPServer(ThreadingUDPServer, BaseSIAServer):
    """Class for a threaded SIA UDP Server."""

    daemon_threads = True
    allow_reuse_address = True

    def __init__(
        self,
        server_address: tuple[str, int],
        accounts: dict[str, SIAAccount],
        func: Callable[[SIAEvent], None],
        counts: Counter,
    ):
        """Create a SIA UDP Server.

        Arguments:
            server_address Tuple[string, int] -- the address the server should listen on.
            accounts Dict[str, SIAAccount] -- accounts as dict with account_id as key, SIAAccount object as value.  # pylint: disable=line-too-long
            func Callable[[SIAEvent], None] -- Function called for each valid SIA event, that can be matched to a account.  # pylint: disable=line-too-long
            counts Counter -- counter kept by client to give insights in how many errorous events were discarded of each type.  # pylint: disable=line-too-long
        """
        ThreadingUDPServer.__init__(self, server_address, SIAUDPHandler)
        BaseSIAServer.__init__(self, accounts, counts, func=func)
