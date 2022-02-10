"""This is a the main class for the SIA Client."""
from __future__ import annotations

from abc import ABC

from .account import SIAAccount
from .base_server import BaseSIAServer
from .utils import CommunicationsProtocol, Counter


class BaseSIAClient(ABC):
    """Base class for SIA Client."""

    def __init__(
        self,
        host: str,
        port: int,
        accounts: list[SIAAccount],
        protocol: CommunicationsProtocol = CommunicationsProtocol.TCP,
    ):
        """Create the SIA Client object.

        Arguments:
            host {str} -- Host to run the server on, usually would be ""
            port {int} -- The port the server listens to.
            accounts {List[SIAAccount]} -- List of SIA Accounts to add.
            # function {Callable[[SIAEvent], None]} -- The function that gets called for each event.
            protocol {CommunicationsProtocol Enum} -- CommunicationsProtocol to use, TCP or UDP.

        """
        self._host = host
        self._port = port
        self.protocol = protocol

        self.sia_server: BaseSIAServer | None = None
        self._accounts: dict[str, SIAAccount]
        self.accounts = accounts

        self._counts = Counter()

    @property
    def accounts(self) -> list[SIAAccount]:
        """Return accounts list, ignoring internal structure.

        Returns:
            List[SIAAccount]: List with SIAAccounts

        """
        return list(self._accounts.values())

    @accounts.setter
    def accounts(self, accounts: list[SIAAccount]) -> None:
        """Set the accounts to monitor.

        Args:
            accounts (List[SIAAccount]): List of SIAAccounts to monitor.

        """
        self._accounts = {a.account_id: a for a in accounts}
        if self.sia_server:
            self.sia_server.accounts = self._accounts

    @property
    def counts(self) -> Counter:
        """Return the counts object."""
        return self._counts
