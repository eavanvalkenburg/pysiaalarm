"""Utils for testing pysiaalarm."""
import logging
from binascii import hexlify
from datetime import datetime, timedelta

import random
from Crypto import Random
from Crypto.Cipher import AES

from pysiaalarm.utils import (
    _load_sia_codes,
)
from pysiaalarm.const import IV

logging.basicConfig(level=logging.INFO)
_LOGGER = logging.getLogger(__name__)

BASIC_CONTENT = f"|Nri<zone>/<code>000]<timestamp>"
BASE_LINE = f'<type>"<seq>L0#<account>[<content>'
UNKNOWN_CODE = "ZX"

KEY = "AAAAAAAAAAAAAAAA"
ACCOUNT = "1111"
HOST = "127.0.0.1"
PORT = 7777

ADM_REVERSE_MAP = {"RP": 1602, "WA": 1113}


def _get_crypter(key: bytes):
    """Give back a encrypter/decrypter."""
    return AES.new(key, AES.MODE_CBC, IV)


def crc_calc(msg: str) -> str:
    """Calculate the CRC of the msg."""
    crc = 0
    for letter in str.encode(msg):
        temp = letter
        for _ in range(0, 8):
            temp ^= crc & 1
            crc >>= 1
            if (temp & 1) != 0:
                crc ^= 0xA001
            temp >>= 1
    return ("%x" % crc).upper().zfill(4)


def _create_padded_message(message):
    """Pad the message."""
    fill_size = len(message) + 16 - len(message) % 16
    return message.zfill(fill_size)


def create_random_line(config):
    """Create a full test line with some random values."""
    return create_test_line(
        account="FFFFFFFFF" if random.random() < 0.1 else config["account_id"],
        key=config["key"],
        code=UNKNOWN_CODE if random.random() < 0.1 else _get_random_code(),
        seq=str(random.randint(1000, 9999)),
        time_offset=timedelta(seconds=random.randint(0, 100)),
        alter_crc=random.random() < 0.1,
    )


def create_line_from_test_case(config, tc):
    """Create a full test line."""
    return create_test_line(
        account="FFFFFFFFF" if tc.get("account", False) else config["account_id"],
        key=config["key"],
        code=UNKNOWN_CODE if tc.get("code", False) else _get_random_code(),
        seq=str(random.randint(1000, 9999)),
        time_offset=timedelta(seconds=100 if tc.get("timestamp", False) else 0),
        alter_crc=tc.get("crc", False),
        wrong_event=tc.get("format", False),
    )


def create_test_line(
    account,
    key,
    code,
    seq="7654",
    time_offset=timedelta(0),
    msg_type="SIA-DCS",
    alter_crc=False,
    alter_key=False,
    wrong_event=False,
    use_fixed_time=False,
):
    """Create a test line, with encrytion if key is supplied."""
    if wrong_event:
        return "This is not a SIA Event."
    timestamp = _get_timestamp(time_offset)
    if use_fixed_time:
        timestamp = "_16:04:02,07-09-2020"
    if key:
        if alter_key:
            _LOGGER.debug("Old key: %s", key)
            key = key[:-1] + str(int(key[-1], 16) - 1)
            _LOGGER.debug("New key: %s", key)
    line = _construct_string(msg_type, seq, account, code, timestamp, key)
    if alter_crc:
        crc = ("%04x" % random.randrange(16 ** 4)).upper()
    else:
        crc = crc_calc(line)
    leng = str(int(str(len(line)), 16)).zfill(4)
    return rf"{crc}{leng}{line}"


def _construct_string(msg_type, seq, account, code, timestamp, key=None):
    """Construct the string based on the inputs."""
    return f'"{"*" if key else ""}{msg_type}"{seq}L0#{account}[{_construct_content(msg_type, "0" if code == "RP" else "1", code, timestamp, key)}'


def _construct_content(msg_type, zone, code, timestamp, key=None):
    """Construct the content of the message."""
    cont = f"]{timestamp}"
    if msg_type == "SIA-DCS":
        cont = f"|Nri{zone}/{code}000" + cont
    if msg_type == "ADM-CID":
        # z = f"{int(zone):03d}"
        cont = f"|{ADM_REVERSE_MAP.get(code)} 00 {int(zone):03d}" + cont
    if key:
        return _encrypt_content(key, cont)
    return cont


def _encrypt_content(key, content):
    """Create encrypted content."""
    if not isinstance(key, bytes):
        key = key.encode("utf-8")
    encrypter = _get_crypter(key)
    extra = len(content) % 16
    unencrypted = (16 - extra) * "0" + content
    return (
        hexlify(encrypter.encrypt(unencrypted.encode("utf-8")))
        .decode(encoding="utf-8")
        .upper()
    )


def _get_timestamp(timed: timedelta) -> str:
    """Create a timestamp in the right format."""
    return (datetime.utcnow() - timed).strftime("_%H:%M:%S,%m-%d-%Y")


def _get_random_code() -> str:
    """Get a random code from all codes."""
    codes = [code for code in _load_sia_codes()]
    return random.choice(codes)
