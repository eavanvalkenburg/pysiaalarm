# -*- coding: utf-8 -*-
"""Class for tests of pysiaalarm."""
import logging
import random
import socket

import pytest
from mock import patch
from pysiaalarm.sia_account import SIAAccount
from pysiaalarm.sia_client import SIAClient
from pysiaalarm.sia_errors import InvalidAccountFormatError
from pysiaalarm.sia_errors import InvalidAccountLengthError
from pysiaalarm.sia_errors import InvalidKeyFormatError
from pysiaalarm.sia_errors import InvalidKeyLengthError
from pysiaalarm.sia_errors import PortInUseError
from pysiaalarm.sia_event import SIAEvent
from test_utils import create_test_items

__author__ = "E.A. van Valkenburg"
__copyright__ = "E.A. van Valkenburg"
__license__ = "mit"

_LOGGER = logging.getLogger(__name__)

BASIC_CONTENT = f"|Nri0/<code>000]_14:26:24,04-15-2020"
BASIC_LINE = f'SIA-DCS"5371L0#<account>[<content>'

KEY = "AAAAAAAAAAAAAAAA"
ACCOUNT = "1111"
HOST = "localhost"
PORT = 7777


def create_test_line(key, account, code, alter_crc=False):
    """Create a test line, with encrytion if key is supplied."""
    content = BASIC_CONTENT.replace("<code>", code)
    if key:
        content = create_test_items(key, content)
    line = f'"{"*" if key else ""}{BASIC_LINE.replace("<account>", account).replace("<content>", content)}'
    crc = SIAEvent.crc_calc(line)
    seq = "0000"
    if alter_crc:
        crc = ("%04x" % random.randrange(16 ** 4)).upper()
    return f"\n{crc}{seq}{line}\r"


def run_fake_client(host, port, message):
    """Run a socker client and send one message."""
    fake_client = socket.create_connection((host, port))
    # fake_client = socket.socket()
    # fake_client.settimeout(1)
    # fake_client.connect((host, port))
    try:
        _LOGGER.debug("Sending message: %s", message)
        fake_client.sendall(message)
        data = fake_client.recv(1024)
        data = bytearray(data)
        _LOGGER.debug(data.decode())
    except Exception as e:
        raise e
    finally:
        fake_client.close()


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
        assert event.account == account
        assert event.type == type

    @pytest.mark.parametrize(
        "key, account, code, alter_crc, count",
        [
            (KEY, ACCOUNT, "RP", False, 1),
            (None, ACCOUNT, "RP", False, 1),
            (None, ACCOUNT, "RP", True, 0),
            (KEY, ACCOUNT, "RP", True, 0),
        ],
    )
    def test_sia_client(self, key, account, code, alter_crc, count):
        """Test sia client behaviour."""
        message = create_test_line(key, account, code, alter_crc)
        _LOGGER.debug(message)
        events = []

        def func_append(event: SIAEvent):
            events.append(event)

        client = SIAClient(
            host="",
            port=PORT,
            accounts=[SIAAccount(account_id=account, key=key)],
            function=func_append,
        )
        client.start()
        run_fake_client(HOST, PORT, message.encode())
        client.stop()

        assert len(events) == count
        if count == 1:
            assert events[0].code == code

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

    @pytest.mark.parametrize("port, error", [(80, PortInUseError), (7777, None)])
    def test_sia_port_errors(self, port, error):
        """Test sia client behaviour."""
        try:
            with patch("pysiaalarm.sia_client.SIAClient.test_port", side_effect=error):
                SIAClient(
                    host="",
                    port=port,
                    accounts=[SIAAccount(account_id=ACCOUNT)],
                    function=func,
                ).test_port()
                assert True if not error else False
        except Exception as exp:
            assert isinstance(exp, error)
