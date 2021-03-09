# -*- coding: utf-8 -*-
"""Class for tests of pysiaalarm."""
import asyncio
import json
import logging
import random

import pytest
from unittest.mock import patch

# from mock import MagicMock, PropertyMock, patch

from pysiaalarm import (
    InvalidAccountFormatError,
    InvalidAccountLengthError,
    InvalidKeyFormatError,
    InvalidKeyLengthError,
    SIAAccount,
    SIAClient,
    SIAEvent,
)
from pysiaalarm.aio import SIAClient as SIAClientA
from pysiaalarm.sia_account import SIAResponseType, _create_padded_message
from pysiaalarm.sia_errors import EventFormatError
from tests.test_alarm_aio import async_send_messages
from tests.test_alarm import send_messages

from .create_line import create_line

logging.basicConfig(level=logging.INFO)
_LOGGER = logging.getLogger(__name__)

KEY = "AAAAAAAAAAAAAAAA"
ACCOUNT = "1111"
HOST = "localhost"
PORT = 7777

# pytestmark = pytest.mark.asyncio


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


class testSIA(object):
    """Class for pysiaalarm tests."""

    pytestmark = pytest.mark.asyncio

    @pytest.mark.parametrize(
        "line, account, type, code, error",
        [
            (
                r'60AB0078"*SIA-DCS"5994L0#AAA[5AB718E008C616BF16F6468033A11326B0F7546CAB230910BCA10E4DEBA42283C436E4F8EFF50931070DDE36D5BB5F0C',
                "AAA",
                None,
                None,
                Exception,
            ),
            (
                r'E5D50078"SIA-DCS"6002L0#AAA[|Nri1/CL501]_14:12:04,09-25-2019',
                "AAA",
                "Closing Report",
                "CL",
                Exception,
            ),
            (
                r'90820051"SIA-DCS"4738R0001L0001[#006969|Nri04/OP001NM]',
                "006969",
                "Opening Report",
                "OP",
                Exception,
            ),
            (
                r'76D80055"*NULL"0000R0L0#AAAB[B4BC8B40D0E6D959D6BEA78E88CC0B2155741A3C44FBB96D476A3E557CAD64D9',
                "AAAB",
                None,
                None,
                Exception,
            ),
            (
                r'C4160279"SIA-DCS"5268L0#AAA[Nri1/WA000]_08:40:47,07-08-2020',
                "AAA",
                "Water Alarm",
                "WA",
                Exception,
            ),
            (r"this is not a parsable event", None, None, None, EventFormatError),
        ],
    )
    @pytest.mark.sync
    def test_event_parsing(self, line, account, type, code, error):
        """Test event parsing methods."""
        try:
            event = SIAEvent(line)
            print(event.sia_string)
            assert event.code == code
            assert event.type == type
            assert event.account == account
            print(event.valid_length)
            print(event.valid_message)
        except Exception as e:
            if error == Exception:
                _LOGGER.debug("Error thrown: %s", e)
                assert False
            if e == error:
                assert True

    # @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "key, account, error",
        [
            ("ZZZZZZZZZZZZZZZZ", ACCOUNT, InvalidKeyFormatError),
            ("158888888888888", ACCOUNT, InvalidKeyLengthError),
            ("1688888888888888", ACCOUNT, None),
            (
                "23888888888888888888888",
                ACCOUNT,
                InvalidKeyLengthError,
            ),
            ("248888888888888888888888", ACCOUNT, None),
            (
                "3188888888888888888888888888888",
                ACCOUNT,
                InvalidKeyLengthError,
            ),
            ("32888888888888888888888888888888", ACCOUNT, None),
            (KEY, "22", InvalidAccountLengthError),
            (KEY, "ZZZ", InvalidAccountFormatError),
        ],
    )
    @pytest.mark.sync
    def test_sia_key_account_errors(self, unused_tcp_port_factory, key, account, error):
        """Test sia client behaviour."""
        try:
            SIAClient(
                host="",
                port=unused_tcp_port_factory(),
                accounts=[SIAAccount(account_id=account, key=key)],
                function=get_func("sync"),
            )
            assert False if error else True
        except Exception as exp:
            assert isinstance(exp, error)

    # @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "config_file, fail_func",
        [
            ("tests\\unencrypted_config.json", False),
            ("tests\\encrypted_config.json", False),
            ("tests\\unencrypted_config.json", True),
            ("tests\\encrypted_config.json", True),
        ],
    )
    @pytest.mark.aio
    async def test_client(
        self, event_loop, unused_tcp_port_factory, config_file, fail_func
    ):
        """Test the client.

        Arguments:
            config_file {str} -- Filename of the config.

        """
        try:
            with open(config_file, "r") as f:
                config = json.load(f)
        except:  # noqa: E722
            config = {"host": HOST, "port": PORT, "account_id": ACCOUNT, "key": None}
        config["port"] = unused_tcp_port_factory()
        events = []

        if fail_func:

            def func_append(event: SIAEvent):
                raise ValueError("test error in user func")

        else:

            def func_append(event: SIAEvent):
                events.append(event)

        siac = SIAClient(
            host="",
            port=config["port"],
            accounts=[SIAAccount(account_id=config["account_id"], key=config["key"])],
            function=func_append,
        )
        siac.start()

        tests = [
            {"code": False, "crc": False, "account": False, "time": False},
            {"code": True, "crc": False, "account": False, "time": False},
            {"code": False, "crc": True, "account": False, "time": False},
            {"code": False, "crc": False, "account": True, "time": False},
            {"code": False, "crc": False, "account": False, "time": True},
        ]

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

    # @pytest.mark.asyncio
    @pytest.mark.aio
    async def test_async_client(self, event_loop, unused_tcp_port_factory):
        """Test the async client."""
        config = {
            "host": HOST,
            "port": unused_tcp_port_factory(),
            "account_id": ACCOUNT,
            "key": KEY,
        }

        events = []

        async def func_append(event: SIAEvent):
            events.append(event)

        siac = SIAClientA(
            host="",
            port=config["port"],
            accounts=[SIAAccount(account_id=config["account_id"], key=config["key"])],
            function=func_append,
        )
        await siac.start()

        tests = [
            {"code": False, "crc": False, "account": False, "time": False},
            {"code": True, "crc": False, "account": False, "time": False},
            {"code": False, "crc": True, "account": False, "time": False},
            {"code": False, "crc": False, "account": True, "time": False},
            {"code": False, "crc": False, "account": False, "time": True},
        ]

        async def run_test():
            await async_send_messages(config, tests, 1)
            await asyncio.sleep(3)

        await run_test()

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
                "user_code": 0,
            },
        }

    @pytest.mark.parametrize(
        ("key, account, code, type, alter_key, wrong_event"),
        [
            (None, "AAA", "RP", "SIA-DCS", False, False),
            (None, "AAA", "WA", "SIA-DCS", False, False),
            ("AAAAAAAAAAAAAAAA", "AAA", "RP", "SIA-DCS", False, False),
            (None, "AAA", "RP", "NULL", False, False),
            ("AAAAAAAAAAAAAAAA", "AAA", "RP", "NULL", False, False),
            ("AAAAAAAAAAAAAAAA", "AAA", "RP", "NULL", True, False),
            ("AAAAAAAAAAAAAAAA", "AAA", "RP", "NULL", False, True),
        ],
    )
    @pytest.mark.sync
    def test_server(self, key, account, code, type, alter_key, wrong_event):
        """Test the server parsing."""
        port_add = random.randint(1, 5)
        config = {
            "host": HOST,
            "port": PORT + port_add,
            "account_id": account,
            "key": key,
        }
        events = []

        def func_append(event: SIAEvent):
            events.append(event)

        siac = SIAClient(
            host="",
            port=config["port"] + port_add,
            accounts=[
                SIAAccount(
                    account_id=config["account_id"],
                    key=config["key"],
                    allowed_timeband=(None, None),
                )
            ],
            function=func_append,
        )

        if alter_key:
            key = key[:-1] + str(int(key[-1], 16) - 1)
        sia_acc = SIAAccount(account, key)
        line = create_line(key, account, sia_acc, code, type)
        if wrong_event:
            line = "This is not a SIA Event."
        _LOGGER.info("Line sent to server: %s", line)
        ev, acc, resp = siac.sia_server.parse_and_check_event(line)
        if alter_key or wrong_event:
            assert ev is None
            assert resp == SIAResponseType.NAK
        else:
            assert resp == SIAResponseType.ACK
            assert acc.account_id == account
            assert ev.account == account
            assert ev.code == code
        # line = create_line(key, account, sia_acc, code, type)
        # ev, acc, resp = siac.sia_server.parse_and_check_event(line)

    @pytest.mark.sync
    def test_accounts(self):
        """Test the account getting and setting."""
        acc_list = [
            SIAAccount(account_id=ACCOUNT, key=KEY, allowed_timeband=(None, None))
        ]
        acc_list2 = [
            SIAAccount(account_id=ACCOUNT, key=KEY, allowed_timeband=(None, None)),
            SIAAccount(account_id="1112", key=KEY, allowed_timeband=(None, None)),
        ]
        siac = SIAClient(
            host="", port=PORT, accounts=acc_list, function=(lambda ev: print(ev))
        )
        assert siac.accounts == acc_list
        siac.accounts = acc_list2
        assert siac.accounts == acc_list2

    # @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("async_func, async_client, error"),
        [
            (False, False, None),
            (False, True, TypeError),
            (True, False, TypeError),
            (True, True, None),
        ],
    )
    @pytest.mark.aio
    def test_func(self, unused_tcp_port_factory, async_func, async_client, error):
        """Test the function setting."""
        acc_list = [
            SIAAccount(account_id=ACCOUNT, key=KEY, allowed_timeband=(None, None))
        ]
        port = unused_tcp_port_factory()
        try:
            if async_client:
                SIAClientA(
                    "",
                    port,
                    acc_list,
                    get_func("aio" if async_func else "sync"),
                )
            else:
                SIAClient(
                    "",
                    port,
                    acc_list,
                    get_func("aio" if async_func else "sync"),
                )
            assert error is None
        except Exception as e:
            if type(e) == error:
                assert True
            else:
                assert False

    # @pytest.mark.asyncio
    @pytest.mark.aio
    # @patch("asyncio.start_server")
    async def test_context(self, event_loop, unused_tcp_port_factory):  # , mock_start):
        """Test the context manager functions."""
        with patch("asyncio.start_server"):
            acc_list = [
                SIAAccount(account_id=ACCOUNT, key=KEY, allowed_timeband=(None, None))
            ]
            with SIAClient(
                HOST, unused_tcp_port_factory(), acc_list, function=get_func("sync")
            ) as cl:
                assert cl.accounts == acc_list

            # test Async
            async with SIAClientA(
                HOST, unused_tcp_port_factory(), acc_list, function=get_func("aio")
            ) as cl:
                assert cl.accounts == acc_list
