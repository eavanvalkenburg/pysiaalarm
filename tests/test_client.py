"""Run a test client."""
import json
import random
import socket
import time
from datetime import datetime
from datetime import timedelta

from pysiaalarm.sia_const import ALL_CODES
from pysiaalarm.sia_event import SIAEvent

from tests.test_utils import create_test_items  # pylint: disable=no-name-in-module

BASIC_CONTENT = f"|Nri0/<code>000]<timestamp>"
BASIC_LINE = f'SIA-DCS"<seq>L0#<account>[<content>'


def get_timestamp(timed) -> str:
    """Create a timestamp in the right format."""
    return (datetime.utcnow() - timed).strftime("_%H:%M:%S,%m-%d-%Y")


def create_test_line(key, account, code, timestamp, alter_crc=False):
    """Create a test line, with encrytion if key is supplied."""
    seq = str(random.randint(1000, 9999))
    content = BASIC_CONTENT.replace("<code>", code).replace("<timestamp>", timestamp)
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


def random_code():
    """Choose a random code."""
    codes = [code for code in ALL_CODES]
    return random.choice(codes)


def random_alter_crc():
    """Choose a random bool for alter_crc."""
    return random.random() < 0.1


def non_existing_code(code):
    """Randomly choose a non-existant code or keep code."""
    return "ZZ" if random.random() < 0.1 else code


def different_account(account):
    """Randomly choose a non-existant account or keep account."""
    return "FFFFFFFFF" if random.random() < 0.1 else account


def client_program(config):
    """Create the socket client and start sending messages every 5 seconds, until stopped, or the server disappears."""
    host = socket.gethostname()  # as both code is running on same pc
    port = config["port"]  # socket server port number

    client_socket = socket.socket()  # instantiate
    client_socket.connect((host, port))  # connect to the server

    while True:
        alter_crc = random_alter_crc()
        code = non_existing_code(random_code())
        account = different_account(config["account_id"])
        timed = timedelta(seconds=random.randint(0, 50))
        timestamp = get_timestamp(timed)
        message = create_test_line(config["key"], account, code, timestamp, alter_crc)
        print(
            f"Message with account: {account}, code: {code}, altered crc: {alter_crc}, timedelta: {timed}"
        )
        print(f"Sending to server: {message}")
        client_socket.send(message.encode())  # send message
        data = client_socket.recv(1024).decode()  # receive response
        print(f"Received from server: {data}")  # show in terminal
        if alter_crc:
            assert len(str.strip(data)) == 0
        elif account == "FFFFFFFFF":
            assert data.find("NAK") > 0
        elif timed.seconds >= 40:
            assert data.find("NAK") > 0
        elif code == "ZZ":
            assert data.find("DUH") > 0
        else:
            assert data.find("ACK") > 0
        time.sleep(5)

    client_socket.close()  # close the connection


if __name__ == "__main__":
    """Run main with a config."""
    with open("local_config.json", "r") as f:
        config = json.load(f)
    client_program(config)
