"""This is a the main class for the SIA Client."""
from abc import ABC, abstractmethod
from typing import Callable, Coroutine, List, Union

from .sia_account import SIAAccount
from .sia_event import SIAEvent


class BaseSIAClient(ABC):
    """Base class for SIA Client."""

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
        self.sia_server = None
        self._host = host
        self._port = port
        self.accounts = accounts
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
    def accounts(self) -> List[SIAAccount]:
        """Return accounts list, ignoring internal structure.

        Returns:
            List[SIAAccount]: List with SIAAccounts

        """
        return list(self._accounts.values())

    @accounts.setter
    def accounts(self, new_accounts: List[SIAAccount]):
        """Set the accounts to monitor.

        Args:
            new_accounts (List[SIAAccount]): List of SIAAccounts to monitor.

        """
        self._accounts = {a.account_id: a for a in new_accounts}
        if self.sia_server:
            self.sia_server.accounts = self._accounts

    @property
    def counts(self):
        """Return the counts dict."""
        return self._counts

    @abstractmethod
    def start(self):
        """Abstract method for start."""

    @abstractmethod
    def stop(self):
        """Abstract method for stop."""
