#!/usr/bin/python
"""Run a test client."""
import asyncio
import json
import logging
import random
import sys
import time
from binascii import hexlify
from datetime import datetime
from datetime import timedelta

from Crypto import Random
from Crypto.Cipher import AES
from pysiaalarm.sia_const import ALL_CODES
from pysiaalarm.sia_event import SIAEvent

BASIC_CONTENT = f"|Nri<zone>/<code>000]<timestamp>"
BASIC_LINE = f'SIA-DCS"<seq>L0#<account>[<content>'


def create_test_items(key, content):
    """Create encrypted content."""
    encrypter = AES.new(
        key.encode("utf8"), AES.MODE_CBC, Random.new().read(AES.block_size)
    )

    extra = len(content) % 16
    unencrypted = (16 - extra) * "0" + content
    return (
        hexlify(encrypter.encrypt(unencrypted.encode("utf8")))
        .decode(encoding="UTF-8")
        .upper()
    )


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
        content = create_test_items(key, content)
    line = f'"{"*" if key else ""}{BASIC_LINE.replace("<account>", account).replace("<content>", content).replace("<seq>", seq)}'
    crc = SIAEvent.crc_calc(line)
    leng = int(str(len(line)), 16)
    pad = (4 - len(str(leng))) * "0"
    length = pad + str(leng)
    if alter_crc:
        crc = ("%04x" % random.randrange(16 ** 4)).upper()
    return f"\n{crc}{length}{line}\r"


CODES = [
    # "BA",
    # "BR",
    # "CA",
    # "CF",
    # "CG",
    # "CL",
    # "CP",
    # "CQ",
    "GA",
    "GH",
    # "NL",
    # "OA",
    # "OG",
    # "OP",
    # "OQ",
    # "OR",
    "RP",
    # "TA",
    "WA",
    "WH",
    # "YG",
]


def random_code(test_case=None):
    """Choose a random code."""
    codes = [code for code in CODES]
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
            return "ZZ"
        else:
            return code
    else:
        return "ZZ" if random.random() < 0.1 else code


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


@asyncio.coroutine
def tcp_client(message, host, port, loop):
    print(f"Trying to send: {message}")

    reader, writer = yield from asyncio.open_connection(host, port, loop=loop)
    writer.write(message.encode())

    data = yield from reader.read(100)
    print(f"Received from server: {data.decode()}")

    writer.close()


def client_program(
    config,
    time_between=3,
    test_case=None,  # [{"code": False, "crc": False, "account": False}]
):
    """Create the socket client and start sending messages every 5 seconds, until stopped, or the server disappears."""
    logging.info("Test client config: %s", config)
    host = config["host"]  # as both code is running on same pc
    port = config["port"]  # socket server port number

    loop = asyncio.get_event_loop()
    task = loop.create_task(
        async_send_messages(host, port, loop, test_case, time_between)
    )
    loop.run_until_complete(task)
    loop.close()


async def async_send_messages(host, port, loop, test_case, time_between):
    stop = False
    cases = len(test_case) if test_case else None
    logging.debug("Number of cases: %s", cases)
    index = 0
    while True and not stop:
        logging.debug("Index: %s", index)
        if cases:
            tc = test_case[index]
        else:
            tc = None
        alter_crc = random_alter_crc(tc)
        code = non_existing_code(random_code(), tc)
        account = different_account(config["account_id"], tc)
        timed = timedelta(seconds=timestamp_offset(tc))
        timestamp = get_timestamp(timed)
        message = create_test_line(config["key"], account, code, timestamp, alter_crc)
        print(
            f"Message with account: {account}, code: {code}, altered crc: {alter_crc}, timedelta: {timed}"
        )
        # loop.create_task(tcp_client(message, host, port, loop))
        await tcp_client(message, host, port, loop)
        if cases:
            if index < cases - 1:
                index += 1
            else:
                stop = True
        await asyncio.sleep(time_between)


if __name__ == "__main__":
    """Run main with a config."""
    logging.info(sys.argv)
    if sys.argv[1]:
        file = sys.argv[1]
    else:
        file = "unencrypted_config.json"
    with open(file, "r") as f:
        config = json.load(f)
    client_program(config)
