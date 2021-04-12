# -*- coding: utf-8 -*-
"""Class for tests of pysiaalarm."""
import logging
import threading
import asyncio
import pytest
from dataclasses import asdict

from pytest_cases import fixture_plus, parametrize_with_cases, fixture
from unittest.mock import patch

from pysiaalarm import (
    SIAAccount,
    SIAClient,
    SIAEvent,
)
from pysiaalarm.aio import SIAClient as SIAClientA
from pysiaalarm.event import NAKEvent
from pysiaalarm.const import COUNTER_USER_CODE, COUNTER_VALID, COUNTER_EVENTS

from tests.test_alarm import send_messages
from tests.test_utils import ACCOUNT, KEY, HOST, create_test_line
from tests.test_sia_package_cases import *  # pylint: disable=W0614


logging.basicConfig(level=logging.INFO)
_LOGGER = logging.getLogger(__name__)


@pytest.fixture
def account():
    """Return default account."""
    return SIAAccount(ACCOUNT, KEY)


@pytest.fixture
def account_list(account):
    """Return default account."""
    return [account]


@fixture(unpack_into="client, config, good, sync")
@pytest.mark.asyncio
@parametrize_with_cases("good", prefix="handler_")
@parametrize_with_cases("key", prefix="encrypted_")
@parametrize_with_cases("sync", prefix="sync_")
@parametrize_with_cases("protocol", prefix="proto_")
def create_client(
    unused_tcp_port_factory,
    event_handler,
    async_event_handler,
    bad_handler,
    async_bad_handler,
    key,
    good,
    protocol,
    sync,
):
    """Fixture to create a SIA Client."""
    config = {
        "host": HOST,
        "port": unused_tcp_port_factory(),
        "account_id": ACCOUNT,
        "key": key,
        "protocol": protocol,
    }

    if sync:
        client = SIAClient(
            host=config["host"],
            port=config["port"],
            accounts=[SIAAccount(config["account_id"], config["key"])],
            function=event_handler if good else bad_handler,
            protocol=config["protocol"],
        )
    else:
        client = SIAClientA(
            host=config["host"],
            port=config["port"],
            accounts=[SIAAccount(config["account_id"], config["key"])],
            function=async_event_handler if good else async_bad_handler,
            protocol=config["protocol"],
        )
    return (client, config, good, sync)


def get_func(type="sync"):
    """Get a test func."""

    async def async_func(event: SIAEvent):
        """Pass for testing."""
        pass

    def func(event: SIAEvent):
        """Pass for testing."""
        pass

    if type == "both":
        return (func, async_func)
    elif type == "aio":
        return async_func
    else:
        return func


@fixture_plus(
    unpack_into="events, event_handler, async_event_handler, bad_handler, async_bad_handler"
)
def get_event_func():
    """Return the handler function."""
    events = []

    async def async_event_handler(event: SIAEvent):
        events.append(event)

    def event_handler(event: SIAEvent):
        events.append(event)

    def bad_handler(_):
        raise ValueError("test error in user func")

    async def async_bad_handler(_):
        raise ValueError("test error in user func")

    return (events, event_handler, async_event_handler, bad_handler, async_bad_handler)


class testSIA(object):
    """Class for pysiaalarm tests."""

    pytestmark = pytest.mark.asyncio

    @parametrize_with_cases("cl, dic, clear_account", cases=ToFromDict)
    def test_to_from_dict(self, cl, dic, clear_account):
        """Test the to and from dict methods."""
        _LOGGER.warning("Dict before: %s", dic)
        instance = cl.from_dict(dic)
        _LOGGER.warning("Class instance %s", instance)
        if cl == SIAAccount:
            assert instance.account_id == dic["account_id"]
            assert instance.key == dic["key"]
            dic2 = instance.to_dict()
        else:
            assert instance.account == dic["account"]
            assert instance.code == dic["code"]
            dic2 = instance.to_dict(encode_json=True)

        _LOGGER.warning("Dict after: %s", dic2)
        for key, value in dic.items():
            if key != "sia_account":
                assert dic2[key] == value
            else:
                if dic[key]:
                    assert instance.sia_account is not None

    @parametrize_with_cases(
        "line, account_id, type, code, error_type, extended_data_flag",
        cases=EventParsing,
    )
    def test_event_parsing(
        self, line, account_id, type, code, error_type, extended_data_flag
    ):
        """Test event parsing methods."""
        try:
            event = SIAEvent.from_line(line)
            # _LOGGER.warning(asdict(event))
            # _LOGGER.warning(event.to_dict())
            # assert False
            assert event.code == code
            if code:
                assert event.sia_code.type == type
            assert event.account == account_id
            if extended_data_flag:
                assert event.extended_data is not None
                if event.extended_data.identifier == "K":
                    event.sia_account = SIAAccount(
                        account_id, KEY, allowed_timeband=None
                    )
                    _LOGGER.debug("RSP Response: %s", event.create_response())
                    assert event.response == ResponseType.RSP
        except Exception as e:
            if error_type is None:
                _LOGGER.debug("Error thrown: %s", e)
                assert False
            if isinstance(e, error_type):
                assert True

    @parametrize_with_cases("key, account_id, error_type", cases=AccountSetup)
    def test_sia_account_setup(
        self, unused_tcp_port_factory, key, account_id, error_type
    ):
        """Test sia client behaviour."""
        try:
            SIAAccount.validate_account(account_id, key)
            SIAClient(
                host="",
                port=unused_tcp_port_factory(),
                accounts=[SIAAccount(account_id=account_id, key=key)],
                function=get_func("sync"),
            )
            assert True if error_type is None else False
        except Exception as exp:
            assert isinstance(exp, error_type)

    @parametrize_with_cases("key, account_id, error_type", cases=AccountSetup)
    def test_sia_account_validation(self, key, account_id, error_type):
        """Test sia account validation."""
        try:
            SIAAccount.validate_account(account_id, key)
            assert True if error_type is None else False
        except Exception as exp:
            assert isinstance(exp, error_type)

    @parametrize_with_cases("fault", prefix="fault_")
    async def test_clients(
        self,
        event_loop,
        unused_tcp_port_factory,
        events,
        client,
        config,
        good,
        sync,
        fault,
    ):
        """Test the clients."""
        if sync:
            client.start()
        else:
            await client.start()
        await asyncio.sleep(0.01)

        t = threading.Thread(
            target=send_messages,
            name="send_messages",
            args=(config, {fault: True}),
        )
        t.daemon = True
        t.start()  # stops after the event has been sent.
        await asyncio.sleep(0.1)

        if sync:
            client.stop()
        else:
            await client.stop()

        _LOGGER.warning("Registered events: %s", client.counts)

        if fault is not None:
            assert client.counts.get(fault) == 1
        else:
            assert client.counts.get(COUNTER_VALID) == 1
        if good and not fault:
            assert len(events) == 1
            assert client.counts.get(COUNTER_EVENTS) == 1
        if not good and not fault:
            assert client.counts.get(COUNTER_USER_CODE) == 1
        if not good or fault:
            assert len(events) == 0

    @parametrize_with_cases("msg_type", prefix="msg_")
    @parametrize_with_cases(
        "code, alter_key, wrong_event, response", cases=ParseAndCheckEvent
    )
    @parametrize_with_cases("key", prefix="encrypted_")
    def test_parse_and_check(
        self,
        unused_tcp_port_factory,
        event_handler,
        key,
        code,
        msg_type,
        alter_key,
        wrong_event,
        response,
    ):
        """Test the server parsing."""
        if msg_type in ("ADM-CID", "NULL") and code == "ZX":
            pytest.skip(
                "Unknown code is not usefull to test in ADM-CID and NULL messages."
            )
            return
        if alter_key and key is None:
            pytest.skip("Alter key is not usefull to test when not encrypted.")
            return

        siac = SIAClient(
            HOST, unused_tcp_port_factory(), [SIAAccount(ACCOUNT, key)], event_handler
        )
        line = create_test_line(
            account=ACCOUNT,
            key=key,
            code=code,
            msg_type=msg_type,
            wrong_event=wrong_event,
            alter_key=alter_key,
        )

        _LOGGER.warning("Line to parse: %s", line)
        event = siac.sia_server.parse_and_check_event(line)
        _LOGGER.warning("Event received: %s", event)

        assert event.response == response
        if wrong_event or alter_key:
            assert isinstance(event, NAKEvent)
        else:
            assert event.account == ACCOUNT
            assert event.code == "RP" if msg_type == "NULL" else code

    def test_accounts_get_set(self, account_list, unused_tcp_port):
        """Test the account getting and setting."""
        siac = SIAClient(
            host="",
            port=unused_tcp_port,
            accounts=account_list,
            function=(lambda ev: print(ev)),
        )
        assert siac.accounts == account_list
        acc_list2 = [
            SIAAccount(account_id=ACCOUNT, key=KEY, allowed_timeband=(None, None)),
            SIAAccount(account_id="1112", key=KEY, allowed_timeband=(None, None)),
        ]
        siac.accounts = acc_list2
        assert siac.accounts == acc_list2

    @parametrize_with_cases("sync_func", prefix="sync_")
    @parametrize_with_cases("sync_client", prefix="sync_")
    def test_func_errors(
        self,
        account_list,
        unused_tcp_port_factory,
        sync_client,
        sync_func,
    ):
        """Test the function setting."""
        error_type = TypeError if sync_client != sync_func else None
        try:
            if sync_client:
                SIAClient(
                    HOST,
                    unused_tcp_port_factory(),
                    account_list,
                    get_func("sync" if sync_func else "aio"),
                )
            else:
                SIAClientA(
                    HOST,
                    unused_tcp_port_factory(),
                    account_list,
                    get_func("sync" if sync_func else "aio"),
                )
            assert error_type is None
        except Exception as e:
            if isinstance(e, error_type):
                assert True
            else:
                assert False

    @parametrize_with_cases("sync", prefix="sync_")
    async def test_context(self, account_list, unused_tcp_port_factory, sync):
        """Test the context manager functions."""
        if sync:
            with patch.object(SIAClient, "stop") as client:
                with SIAClient(
                    HOST,
                    unused_tcp_port_factory(),
                    account_list,
                    function=get_func("sync"),
                ) as cl:
                    assert cl.accounts == account_list
                client.assert_called_once()

        else:
            with patch.object(SIAClientA, "stop") as client:
                with patch("asyncio.start_server"):
                    # test Async
                    async with SIAClientA(
                        HOST,
                        unused_tcp_port_factory(),
                        account_list,
                        function=get_func("aio"),
                    ) as cl:
                        assert cl.accounts == account_list
                client.assert_awaited_once()
