# -*- coding: utf-8 -*-
"""Class for tests of pysiaalarm."""
import asyncio
import json
import logging
import random
import re
import socket
import threading
import time
from typing import Type

import pytest
from hypothesis import example, given, settings
from hypothesis import strategies as st
from mock import MagicMock, PropertyMock, patch

from pysiaalarm import (
    InvalidAccountFormatError,
    InvalidAccountLengthError,
    InvalidKeyFormatError,
    InvalidKeyLengthError,
    SIAAccount,
    SIAClient,
    SIAEvent,
    sia_event,
)
from pysiaalarm.aio import SIAClient as SIAClientA
from pysiaalarm.sia_account import SIAResponseType, _create_padded_message
from pysiaalarm.sia_errors import EventFormatError
from tests.test_alarm_aio import async_send_messages

# from tests.test_utils import create_test_item

from .create_line import create_line

logging.basicConfig(level=logging.INFO)
_LOGGER = logging.getLogger(__name__)

KEY = "AAAAAAAAAAAAAAAA"
ACCOUNT = "1111"
HOST = "localhost"
PORT = 7777


def func(event: SIAEvent):
    """Pass for testing."""
    pass


class testSIA(object):
    """Class for pysiaalarm tests."""

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

    @pytest.mark.parametrize(
        "key, account, port, error",
        [
            ("ZZZZZZZZZZZZZZZZ", ACCOUNT, 7777, InvalidKeyFormatError),
            ("158888888888888", ACCOUNT, 7777, InvalidKeyLengthError),
            ("1688888888888888", ACCOUNT, 7777, None),
            ("23888888888888888888888", ACCOUNT, 7777, InvalidKeyLengthError),
            ("248888888888888888888888", ACCOUNT, 7777, None),
            ("3188888888888888888888888888888", ACCOUNT, 7777, InvalidKeyLengthError),
            ("32888888888888888888888888888888", ACCOUNT, 7777, None),
            (KEY, "22", 7777, InvalidAccountLengthError),
            (KEY, "ZZZ", 7777, InvalidAccountFormatError),
        ],
    )
    def test_sia_key_account_errors(self, key, account, port, error):
        """Test sia client behaviour."""
        try:
            SIAClient(
                host="",
                port=port,
                accounts=[SIAAccount(account_id=account, key=key)],
                function=func,
            )
            assert False if error else True
        except Exception as exp:
            assert isinstance(exp, error)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "config_file, port_add, fail_func",
        [
            ("tests\\unencrypted_config.json", 1, False),
            ("tests\\encrypted_config.json", 2, False),
            ("tests\\unencrypted_config.json", 3, True),
            ("tests\\encrypted_config.json", 4, True),
        ],
    )
    async def test_client(self, config_file, port_add, fail_func):
        """Test the client.

        Arguments:
            config_file {str} -- Filename of the config.

        """
        try:
            with open(config_file, "r") as f:
                config = json.load(f)
        except:  # noqa: E722
            config = {"host": HOST, "port": PORT, "account_id": ACCOUNT, "key": None}
        config["port"] = config["port"] + port_add
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
        # t = threading.Thread(
        #     target=client_program, name="test_client", args=(config, 1, tests)
        # )
        # t.daemon = True
        # t.start()  # stops after the five events have been sent.

        # # run for 7 seconds
        # time.sleep(10)

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

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "config_file, port_add, fail_func",
        [
            ("tests\\unencrypted_config.json", 5, False),
            ("tests\\encrypted_config.json", 6, False),
            ("tests\\unencrypted_config.json", 7, True),
            ("tests\\encrypted_config.json", 8, True),
        ],
    )
    async def test_async_client(self, config_file, port_add, fail_func):
        """Test the client.

        Arguments:
            config_file {str} -- Filename of the config.

        """
        try:
            with open(config_file, "r") as f:
                config = json.load(f)
        except:  # noqa: E722
            config = {"host": HOST, "port": PORT, "account_id": ACCOUNT, "key": None}
        config["port"] = config["port"] + port_add
        events = []

        if fail_func:

            async def func_append(event: SIAEvent):
                raise ValueError("test error in user func")

        else:

            async def func_append(event: SIAEvent):
                events.append(event)

        siac = SIAClientA(
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

        # t = threading.Thread(
        #     target=client_program, name="test_client", args=(config, 1, tests)
        # )
        # t.daemon = True
        # t.start()  # stops after the five events have been sent.

        # run for 7 seconds, so sleep for 10
        # await asyncio.sleep(10)

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
    def test_server(self, key, account, code, type, alter_key, wrong_event):
        """Test the server parsing."""
        config = {"host": HOST, "port": PORT, "account_id": account, "key": key}
        events = []

        def func_append(event: SIAEvent):
            events.append(event)

        siac = SIAClient(
            host="",
            port=config["port"],
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
        line = create_line(key, account, sia_acc, code, type)
        ev, acc, resp = siac.sia_server.parse_and_check_event(line)

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

    @pytest.mark.parametrize(
        ("async_func, async_client, error"),
        [
            (False, False, None),
            (False, True, None),
            (True, False, TypeError),
            (True, True, None),
        ],
    )
    def test_func(self, async_func, async_client, error):
        """Test the function setting."""
        acc_list = [
            SIAAccount(account_id=ACCOUNT, key=KEY, allowed_timeband=(None, None))
        ]
        if async_func:

            async def func(event):
                pass

        else:

            def func(event):
                pass

        try:
            if async_client:
                SIAClientA("", PORT, acc_list, func)
            else:
                SIAClient("", PORT, acc_list, func)
            assert error is None
        except error:
            assert error is not None
        except Exception:
            assert False

    @pytest.mark.asyncio
    async def test_context(self):
        """Test the context manager functions."""

        def func(ev):
            print(ev)

        async def async_func(ev):
            print(ev)

        acc_list = [
            SIAAccount(account_id=ACCOUNT, key=KEY, allowed_timeband=(None, None))
        ]
        with SIAClient(HOST, PORT, acc_list, function=func) as cl:
            assert cl.accounts == acc_list

        # test with Async func
        async with SIAClientA(HOST, PORT, acc_list, function=async_func) as cl:
            assert cl.accounts == acc_list

        # test with sync func in async package
        try:
            async with SIAClientA(HOST, PORT + 1, acc_list, function=func) as cl:
                assert cl.accounts == acc_list
        except TypeError:
            _LOGGER.debug("Expected type error.")

    content = st.text(
        st.characters(min_codepoint=32, max_codepoint=126), min_size=4, max_size=15
    ).filter(lambda x: bool(re.fullmatch(r"^(?![0]+).*(?<![0]{1,14})$", x)))
    # ^(?=.*\d)(?=.*[B-Zb-z]{2,}).*$
    key = st.from_regex(
        regex=r"^[0-9A-E]{16}$|^[0-9A-E]{24}$|^[0-9A-E]{32}$", fullmatch=True
    )

    # @given(key, content)
    # @example("AAAAAAAAAAAAAAAA", "|Nri1/GH000]_12:16:13,07-16-2020")
    # @example("AAAAAAAAAAAAAAAA", "|Nri1/ZW000]_12:30:51,07-16-2020")
    # def test_encrypt_decrypt(self, key, content):
    #     """Test encryption and decryption."""
    #     _LOGGER.debug("Key: %s", key)
    #     acc = SIAAccount(ACCOUNT, key)
    #     _LOGGER.debug("Unencrypted message: %s", content)
    #     message = acc.encrypt(content)
    #     with patch("pysiaalarm.SIAEvent") as event:
    #         type(event).encrypted_content = PropertyMock(return_value=message)
    #         _LOGGER.debug("Encrypted message event: %s", event.encrypted_content)
    #         decrypted_event = acc.decrypt(event)
    #         _LOGGER.debug("Decrypted message: %s", decrypted_event.content)
    #         out_content = decrypted_event.content[-len(content) :]
    #         assert out_content == content
