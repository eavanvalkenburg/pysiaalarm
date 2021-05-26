"""This is a the main class for the SIA Client."""
from abc import ABC, abstractmethod
from typing import Any, Callable, Coroutine, List, Union

from .account import SIAAccount
from .event import SIAEvent
from .utils import CommunicationsProtocol, Counter


class BaseSIAClient(ABC):
    """Base class for SIA Client."""

    def __init__(
        self,
        host: str,
        port: int,
        accounts: List[SIAAccount],
        function: Callable[[SIAEvent], None],
        protocol: CommunicationsProtocol = CommunicationsProtocol.TCP,
    ):
        """Create the SIA Client object.

        Arguments:
            host {str} -- Host to run the server on, usually would be ""
            port {int} -- The port the server listens to.
            accounts {List[SIAAccount]} -- List of SIA Accounts to add.
            function {Callable[[SIAEvent], None]} -- The function that gets called for each event.
            protocol {CommunicationsProtocol Enum} -- CommunicationsProtocol to use, TCP or UDP.

        """
        self.sia_server: Any = None
        self._host = host
        self._port = port
        self.protocol = protocol
        self.accounts = accounts
        self._func = function

        self._counts = Counter()

    @property
    def accounts(self) -> List[SIAAccount]:
        """Return accounts list, ignoring internal structure.

        Returns:
            List[SIAAccount]: List with SIAAccounts

        """
        return list(self._accounts.values())

    @accounts.setter
    def accounts(self, new_accounts: List[SIAAccount]) -> None:
        """Set the accounts to monitor.

        Args:
            new_accounts (List[SIAAccount]): List of SIAAccounts to monitor.

        """
        self._accounts = {a.account_id: a for a in new_accounts}
        if self.sia_server:
            self.sia_server.accounts = self._accounts

    @property
    def counts(self) -> Counter:
        """Return the counts object."""
        return self._counts

    @abstractmethod
    def start(self, **kwargs: Any) -> Union[None, Coroutine[Any, Any, None]]:
        """Abstract method for start."""
        pass  # pragma: no cover

    @abstractmethod
    def stop(self) -> Union[None, Coroutine[Any, Any, None]]:
        """Abstract method for stop."""
        pass  # pragma: no cover
