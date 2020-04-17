# -*- coding: utf-8 -*-
"""Class for tests of pysiaalarm."""

import pytest
import socket
import logging
import random
from pysiaalarm.sia_client import SIAClient
from pysiaalarm.sia_event import SIAEvent
from .test_utils import create_test_items

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
    fake_client = socket.socket()
    fake_client.settimeout(1)
    fake_client.connect((host, port))
    try:
        fake_client.send(message)
    except Exception as e:
        raise e
    finally:
        fake_client.close()


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

        def func(event: SIAEvent):
            events.append(event)

        client = SIAClient(
            host="", port=PORT, account_id=account, key=key, function=func
        )

        client.start()

        run_fake_client(HOST, PORT, message.encode())

        client.stop()

        assert len(events) == count
        if count == 1:
            assert events[0].code == code
