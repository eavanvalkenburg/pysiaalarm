# -*- coding: utf-8 -*-
"""Class for tests of pysiaalarm."""
import logging
import threading
import asyncio
import pytest

from pytest_cases import fixture_plus, parametrize_with_cases
from unittest.mock import patch

from pysiaalarm import (
    SIAAccount,
    SIAClient,
    SIAEvent,
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


@fixture_plus(unpack_into="events, event_handler, async_event_handler")
def get_event_func_factory():
    events = []

    async def async_event_handler(event: SIAEvent):
        events.append(event)

    def event_handler(event: SIAEvent):
        events.append(event)

    return (events, event_handler, async_event_handler)


class testSIA(object):
    """Class for pysiaalarm tests."""

    pytestmark = pytest.mark.asyncio

    @pytest.mark.sync
    @parametrize_with_cases("line, account_id, type, code, error", cases=EventParsing)
    def test_event_parsing(self, line, account_id, type, code, error):
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
            if error == Exception:
                _LOGGER.debug("Error thrown: %s", e)
                assert False
            if e == error:
                assert True

    @pytest.mark.sync
    @parametrize_with_cases("key, account_id, error", cases=AccountSetup)
    def test_sia_account_setup(self, unused_tcp_port_factory, key, account_id, error):
        """Test sia client behaviour."""
        try:
            SIAClient(
                host="",
                port=unused_tcp_port_factory(),
                accounts=[SIAAccount(account_id=account_id, key=key)],
                function=get_func("sync"),
            )
            assert False if error else True
        except Exception as exp:
            assert isinstance(exp, error)

    @pytest.mark.aio
    @parametrize_with_cases("config, fail_func", cases=TestClient)
    async def test_client(
        self,
        event_loop,
        unused_tcp_port_factory,
        events,
        event_handler,
        tests,
        config,
        fail_func,
    ):
        """Test the client."""
        config["port"] = unused_tcp_port_factory()
        if fail_func:

            def event_handler(event: SIAEvent):
                raise ValueError("test error in user func")

        siac = SIAClient(
            host=config["host"],
            port=config["port"],
            accounts=[SIAAccount(account_id=config["account_id"], key=config["key"])],
            function=event_handler,
        )
        siac.start()
        await async_send_messages(config, tests, 1)
        siac.stop()
        assert siac.counts == {
            "events": 5,
            "valid_events": 1,
            "errors": {
                "crc": 1,
                "timestamp": 1,
                "account": 1,
                "code": 1,
                "format": 0,
                "user_code": 1 if fail_func else 0,
            },
        }
        assert len(events) == 0 if fail_func else 1

    @pytest.mark.aio
    @parametrize_with_cases("config, fail_func", cases=TestClient)
    async def test_async_client(
        self,
        event_loop,
        unused_tcp_port_factory,
        tests,
        events,
        async_event_handler,
        config,
        fail_func,
    ):
        """Test the async client."""
        # config = {
        #     "host": '127.0.0.1',
        #     "port": unused_tcp_port_factory(),
        #     "account_id": account.account_id,
        #     "key": account.key,
        # }

        config["port"] = unused_tcp_port_factory()
        if fail_func:

            async def async_event_handler(event: SIAEvent):
                raise ValueError("test error in user func")

        siac = SIAClientA(
            host=config["host"],
            port=config["port"],
            accounts=[SIAAccount(account_id=config["account_id"], key=config["key"])],
            function=async_event_handler,
        )
        await siac.start()

        def run_test():
            send_messages(config, tests, 1)

        # await asyncio.gather(
        #     asyncio.to_thread(run_test),
        #     asyncio.sleep(10),
        # )

        # await run_test()
        t = threading.Thread(target=run_test, name="send_messages")
        t.daemon = True
        t.start()  # stops after the five events have been sent.

        # run for 7 seconds
        await asyncio.sleep(10)
        _LOGGER.debug("Registered events: %s", siac.counts)

        await siac.stop()
        assert siac.counts == {
            "events": 5,
            "valid_events": 1,
            "errors": {
                "crc": 1,
                "timestamp": 1,
                "account": 1,
                "code": 1,
                "format": 0,
                "user_code": 1 if fail_func else 0,
            },
        }
        assert len(events) == 0 if fail_func else 1

    @pytest.mark.sync
    @parametrize_with_cases(
        "account_id, key, code, msg_type, alter_key, wrong_event, response",
        cases=ParseAndCheckEvent,
    )
    def test_parse_and_check(
        self,
        unused_tcp_port_factory,
        event_handler,
        account_id,
        key,
        code,
        msg_type,
        alter_key,
        wrong_event,
        response,
    ):
        """Test the server parsing."""
        acc = SIAAccount(account_id, key)
        siac = SIAClient(HOST, unused_tcp_port_factory(), [acc], event_handler)
        line = create_test_line(
            account=account_id,
            key=key,
            code=code,
            msg_type=msg_type,
            wrong_event=wrong_event,
            alter_key=alter_key,
        )
        _LOGGER.info("Line to parse: %s", line)

        ev, acc, resp = siac.sia_server.parse_and_check_event(line)
        assert resp == response
        if wrong_event:
            assert ev is None
        elif alter_key:
            assert ev.account == account_id
            assert ev.encrypted == True
            assert ev.encrypted_content is not None
        else:
            assert acc.account_id == account_id
            assert ev.account == account_id
            assert ev.code == code

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
    @parametrize_with_cases("async_func, async_client, error_type", cases=FuncErrors)
    def test_func_errors(
        self,
        account_list,
        unused_tcp_port_factory,
        async_client,
        async_func,
        error_type,
    ):
        """Test the function setting."""
        try:
            if async_client:
                SIAClientA(
                    HOST,
                    unused_tcp_port_factory(),
                    account_list,
                    get_func("aio" if async_func else "sync"),
                )
            else:
                SIAClient(
                    HOST,
                    unused_tcp_port_factory(),
                    account_list,
                    get_func("aio" if async_func else "sync"),
                )
            assert error_type is None
        except Exception as e:
            if type(e) == error_type:
                assert True
            else:
                assert False

    @pytest.mark.aio
    async def test_context(self, account_list, unused_tcp_port_factory):
        """Test the context manager functions."""
        with patch("asyncio.start_server"):
            with SIAClient(
                HOST, unused_tcp_port_factory(), account_list, function=get_func("sync")
            ) as cl:
                assert cl.accounts == account_list

            # test Async
            async with SIAClientA(
                HOST, unused_tcp_port_factory(), account_list, function=get_func("aio")
            ) as cl:
                assert cl.accounts == account_list
