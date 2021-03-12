# -*- coding: utf-8 -*-
"""Class for tests of pysiaalarm."""
import logging
import threading
import asyncio
import pytest

from pytest_cases import fixture_plus, parametrize_with_cases, fixture
from unittest.mock import patch

from pysiaalarm import (
    SIAAccount,
    SIAClient,
    SIAEvent,
    Protocol,
)
from pysiaalarm.aio import SIAClient as SIAClientA

from tests.test_alarm_aio import async_send_messages
from tests.test_alarm import send_messages
from tests.test_utils import ACCOUNT, KEY, HOST, create_test_line
from tests.test_sia_package_cases import *


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
@parametrize_with_cases("protocol", prefix="proto_")  # , glob="*tcp")
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


@pytest.fixture
def tests():
    """Return test list."""
    return [
        {"code": False, "crc": False, "account": False, "time": False},
        {"code": True, "crc": False, "account": False, "time": False},
        {"code": False, "crc": True, "account": False, "time": False},
        {"code": False, "crc": False, "account": True, "time": False},
        {"code": False, "crc": False, "account": False, "time": True},
    ]


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


@fixture
def events():
    """Return an empty list to store events in a handler function."""
    return []


@fixture_plus(
    unpack_into="event_handler, async_event_handler, bad_handler, async_bad_handler"
)
def get_event_func(events):
    async def async_event_handler(event: SIAEvent):
        events.append(event)

    def event_handler(event: SIAEvent):
        events.append(event)

    def bad_handler(_):
        raise ValueError("test error in user func")

    async def async_bad_handler(_):
        raise ValueError("test error in user func")

    return (event_handler, async_event_handler, bad_handler, async_bad_handler)


class testSIA(object):
    """Class for pysiaalarm tests."""

    pytestmark = pytest.mark.asyncio

    @pytest.mark.sync
    @parametrize_with_cases(
        "line, account_id, type, code, error_type", cases=EventParsing
    )
    def test_event_parsing(self, line, account_id, type, code, error_type):
        """Test event parsing methods."""
        try:
            event = SIAEvent(line)
            print(event.sia_string)
            assert event.code == code
            assert event.type == type
            assert event.account == account_id
            print(event.valid_length)
            print(event.valid_message)
        except Exception as e:
            if error_type is None:
                _LOGGER.debug("Error thrown: %s", e)
                assert False
            if isinstance(e, error_type):
                assert True

    @pytest.mark.sync
    @parametrize_with_cases("key, account_id, error_type", cases=AccountSetup)
    def test_sia_account_setup(
        self, unused_tcp_port_factory, key, account_id, error_type
    ):
        """Test sia client behaviour."""
        try:
            SIAClient(
                host="",
                port=unused_tcp_port_factory(),
                accounts=[SIAAccount(account_id=account_id, key=key)],
                function=get_func("sync"),
            )
            assert True if error_type is None else False
        except Exception as exp:
            assert isinstance(exp, error_type)

    @pytest.mark.aio
    async def test_clients(
        self,
        event_loop,
        unused_tcp_port_factory,
        events,
        client,
        config,
        good,
        sync,
        tests,
    ):
        """Test the clients."""

        if sync:
            client.start()
        else:
            await client.start()
        await asyncio.sleep(0.01)

        t = threading.Thread(
            target=send_messages, name="send_messages", args=(config, tests, 0.0001)
        )
        t.daemon = True
        t.start()  # stops after the five events have been sent.

        await asyncio.sleep(5)
        _LOGGER.debug("Registered events: %s", client.counts)

        if sync:
            client.stop()
        else:
            await client.stop()

        assert client.counts == {
            "events": 5,
            "valid_events": 1,
            "errors": {
                "crc": 1,
                "timestamp": 1,
                "account": 1,
                "code": 1,
                "format": 0,
                "user_code": 0 if good else 1,
            },
        }
        if good:
            assert len(events) == 1
        if not good:
            assert len(events) == 0

    @pytest.mark.sync
    @parametrize_with_cases("msg_type", prefix="msg_")
    @parametrize_with_cases(
        "code, alter_key, wrong_event, response",
        cases=ParseAndCheckEvent,
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

        ev, acc, resp = siac.sia_server.parse_and_check_event(line)

        if wrong_event:
            assert ev is None
            if isinstance(response, list):
                assert resp in response
            else:
                assert resp == response
        elif alter_key and key is not None:
            assert ev.account == ACCOUNT
            assert ev.encrypted == True
            assert ev.encrypted_content is not None
            if msg_type == "SIA-DCS":
                if isinstance(response, list):
                    assert resp in response
                else:
                    assert resp == response
        else:
            if not alter_key:
                if isinstance(response, list):
                    assert resp in response
                else:
                    assert resp == response
            assert acc.account_id == ACCOUNT
            assert ev.account == ACCOUNT
            assert ev.code == code if msg_type == "SIA-DCS" else "RP"

    @pytest.mark.sync
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

    @pytest.mark.aio
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

    @pytest.mark.aio
    @parametrize_with_cases("sync", prefix="sync_")
    async def test_context(self, account_list, unused_tcp_port_factory, sync):
        """Test the context manager functions."""
        if sync:
            with SIAClient(
                HOST, unused_tcp_port_factory(), account_list, function=get_func("sync")
            ) as cl:
                assert cl.accounts == account_list
        else:
            with patch("asyncio.start_server"):
                # test Async
                async with SIAClientA(
                    HOST,
                    unused_tcp_port_factory(),
                    account_list,
                    function=get_func("aio"),
                ) as cl:
                    assert cl.accounts == account_list
