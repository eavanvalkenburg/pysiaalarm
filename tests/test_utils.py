"""Utils for testing pysiaalarm."""
import time
from binascii import hexlify, unhexlify
from datetime import datetime, timedelta

import random
from Crypto import Random
from Crypto.Cipher import AES

from pysiaalarm.sia_event import SIAEvent
from pysiaalarm.sia_const import ALL_CODES

BASIC_CONTENT = f"|Nri<zone>/<code>000]<timestamp>"
BASIC_LINE = f'SIA-DCS"<seq>L0#<account>[<content>'


def create_test_item(key, content):
    """Create encrypted content."""
    encrypter = AES.new(
        key.encode("utf-8"), AES.MODE_CBC, unhexlify("00000000000000000000000000000000")
    )

    extra = len(content) % 16
    unencrypted = (16 - extra) * "0" + content
    return (
        hexlify(encrypter.encrypt(unencrypted.encode("utf-8")))
        .decode(encoding="utf-8")
        .upper()
    )


def create_line(config, tc=None):
    """Create a full test line."""
    alter_crc = random_alter_crc(tc)
    code = non_existing_code(random_code(), tc)
    account = different_account(config["account_id"], tc)
    timed = timedelta(seconds=timestamp_offset(tc))
    timestamp = get_timestamp(timed)
    return create_test_line(config["key"], account, code, timestamp, alter_crc)


def get_timestamp(timed) -> str:
    """Create a timestamp in the right format."""
    return (datetime.utcnow() - timed).strftime("_%H:%M:%S,%m-%d-%Y")


def create_test_line(key, account, code, timestamp, alter_crc=False):
    """Create a test line, with encrytion if key is supplied."""
    seq = str(random.randint(1000, 9999))
    content = (
        BASIC_CONTENT.replace("<zone>", "0" if code == "RP" else "1")
        .replace("<code>", code)
        .replace("<timestamp>", timestamp)
    )
    if key:
        content = create_test_item(key, content)
    line = f'"{"*" if key else ""}{BASIC_LINE.replace("<account>", account).replace("<content>", content).replace("<seq>", seq)}'
    crc = SIAEvent.crc_calc(line)
    leng = int(str(len(line)), 16)
    pad = (4 - len(str(leng))) * "0"
    length = pad + str(leng)
    if alter_crc:
        crc = ("%04x" % random.randrange(16 ** 4)).upper()
    return f"\n{crc}{length}{line}\r"


# CODES = [
#     "AT",
#     "AR",
#     "BA",
#     "BR",
#     "CA",
#     "CF",
#     "CG",
#     "CL",
#     "CP",
#     "CQ",
#     "GA",
#     "GH",
#     "FA",
#     "FH",
#     "KA",
#     "KH",
#     "NL",
#     "OA",
#     "OG",
#     "OP",
#     "OQ",
#     "OR",
#     "RP",
#     "TA",
#     "WA",
#     "WH",
#     "YG",
# ]


def random_code(test_case=None):
    """Choose a random code."""
    codes = [code for code in ALL_CODES]
    return random.choice(codes)


def random_alter_crc(test_case=None):
    """Choose a random bool for alter_crc."""
    if test_case:
        if test_case.get("crc"):
            return True
        else:
            return False
    else:
        return random.random() < 0.1


def non_existing_code(code, test_case=None):
    """Randomly choose a non-existant code or keep code."""
    if test_case:
        if test_case.get("code"):
            return "ZX"
        else:
            return code
    else:
        return "ZX" if random.random() < 0.1 else code


def different_account(account, test_case=None):
    """Randomly choose a non-existant account or keep account."""
    if test_case:
        if test_case.get("account"):
            return "FFFFFFFFF"
        else:
            return account
    else:
        return "FFFFFFFFF" if random.random() < 0.1 else account


def timestamp_offset(test_case=None):
    """Create timestamp offset for testing."""
    if test_case:
        if test_case.get("time"):
            return 100
        else:
            return 0
    else:
        return random.randint(0, 60)
