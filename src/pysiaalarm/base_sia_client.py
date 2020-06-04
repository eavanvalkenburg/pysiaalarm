"""This is a the main class for the SIA Client."""
import logging
from abc import ABC
from abc import abstractmethod
from typing import Callable
from typing import List

from .sia_account import SIAAccount
from .sia_event import SIAEvent


class BaseSIAClient(ABC):
    def __init__(
        self,
        host: str,
        port: int,
        accounts: List[SIAAccount],
        function: Callable[[SIAEvent], None],
    ):
        """Create the SIA Client object.

        Arguments:
            host {str} -- Host to run the server on, usually would be ""
            port {int} -- The port the server listens to.
            accounts {List[SIAAccount]} -- List of SIA Accounts to add.
            function {Callable[[SIAEvent], None]} -- The function that gets called for each event.

        """
        self._host = host
        self._port = port
        self._accounts = {a.account_id: a for a in accounts}
        self._func = function
        self._counts = {
            "events": 0,
            "valid_events": 0,
            "errors": {
                "crc": 0,
                "timestamp": 0,
                "account": 0,
                "code": 0,
                "format": 0,
                "user_code": 0,
            },
        }

    @property
    def counts(self):
        """Return the counts dict."""
        return self._counts

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def stop(self):
        pass
