import binascii
import json
import logging
import random
import socket
import sys
import time
from binascii import hexlify
from datetime import datetime, timedelta

from Crypto import Random
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

from pysiaalarm import SIAAccount, SIAEvent
from pysiaalarm.sia_account import _create_padded_message
from pysiaalarm.sia_const import ALL_CODES

BASIC_CONTENT = f"|Nri<zone>/<code>000]<timestamp>"
BASIC_LINE = f'SIA-DCS"<seq>L0#<account>[<content>'
NULL_LINE = f'NULL"<seq>L0#<account>[<content>'

_LOGGER = logging.getLogger(__name__)


def create_line(
    key, account, code, type="SIA-DCS", generate=True, timestamp=None, alter_crc=False
):
    acc = SIAAccount(account, key)
    if generate:
        seq = str(random.randint(1000, 9999))
        timestamp = (
            timestamp
            if timestamp
            else (datetime.utcnow()).strftime("_%H:%M:%S,%m-%d-%Y")
        )
    else:
        seq = "7654"
        timestamp = "_16:04:02,07-09-2020"
    if type == "SIA-DCS":
        content = (
            BASIC_CONTENT.replace("<zone>", "0" if code == "RP" else "1")
            .replace("<code>", code)
            .replace("<timestamp>", timestamp)
        )
        base_line = BASIC_LINE
    else:
        content = f"]{timestamp}"
        if key:
            content = _create_padded_message(content)
        base_line = NULL_LINE
    content = acc.encrypt(content)

    line = f'"{"*" if key else ""}{base_line.replace("<account>", account).replace("<content>", content).replace("<seq>", seq)}'

    crc = SIAEvent.crc_calc(line)
    if alter_crc:
        crc = ("%04x" % random.randrange(16 ** 4)).upper()
    leng = str(int(str(len(line)), 16)).zfill(4)
    return rf"{crc}{leng}{line}"
