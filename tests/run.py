import json
import logging
import os
import time

from pysiaalarm import SIAAccount
from pysiaalarm import SIAClient
from pysiaalarm import SIAEvent

logging.basicConfig(level=logging.DEBUG)

events = []


def func(event: SIAEvent):
    events.append(event)


with open("unencrypted_config.json", "r") as f:
    config = json.load(f)

client = SIAClient(
    config["host"],
    config["port"],
    [SIAAccount(config["account_id"], config["key"])],
    function=func,
)

client.start()

sleep_time = 120
print("--------------------------------------------------")
print(f"Client started... will run for {sleep_time} seconds")
time.sleep(sleep_time)
print(f"Client will stop now...")
print("--------------------------------------------------")
client.stop()

# for ev in events:
#     print(ev)

print("--------------------------------------------------")
print(len(events))
print(client.counts)
print("--------------------------------------------------")
