# -*- coding: utf-8 -*-
"""Class for tests of pysiaalarm."""
import json
import logging
import random
import socket
import threading
import time

import pytest
from mock import patch
from pysiaalarm import InvalidAccountFormatError
from pysiaalarm import InvalidAccountLengthError
from pysiaalarm import InvalidKeyFormatError
from pysiaalarm import InvalidKeyLengthError
from pysiaalarm import SIAAccount
from pysiaalarm import SIAClient
from pysiaalarm import SIAEvent

from tests.test_client import client_program
from tests.test_utils import create_test_items

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
        "line, account, type, code",
        [
            (
                '98100078"*SIA-DCS"5994L0#AAA[5AB718E008C616BF16F6468033A11326B0F7546CAB230910BCA10E4DEBA42283C436E4F8EFF50931070DDE36D5BB5F0C',
                "AAA",
                "",
                "",
            ),
            (
                '2E680078"SIA-DCS"6002L0#AAA[|Nri1/CL501]_14:12:04,09-25-2019',
                "AAA",
                "Closing Report",
                "CL",
            ),
        ],
    )
    def test_event_parsing(self, line, account, type, code):
        """Test event parsing methods."""
        event = SIAEvent(line)
        assert event.code == code
        assert event.type == type
        assert event.account == account

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

    @pytest.mark.parametrize("config_file", [("tests\\unencrypted_config.json")])
    def test_client(self, config_file):
        """Test the client.

        Arguments:
            config_file {str} -- Filename of the config.

        """
        try:
            with open(config_file, "r") as f:
                config = json.load(f)
        except:  # noqa: E722
            config = {"host": HOST, "port": PORT, "account_id": ACCOUNT, "key": None}

        events = []

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

        t = threading.Thread(
            target=client_program, name="test_client", args=(config, 1, tests)
        )
        t.daemon = True
        t.start()  # stops after the five events have been sent.

        # run for 30 seconds
        time.sleep(30)

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
                "user_code": 0,
            },
        }
        assert len(events) == 1
