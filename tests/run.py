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

account = [SIAAccount(config["account_id"], config["key"])]
client = SIAClient(config["host"], config["port"], account, function=func)
sleep_time = 120

client.start()

time.sleep(20)
print(f"Client started... adding extra account")
accounts = client.accounts
accounts.append(SIAAccount("FFFFFFFFF", config["key"]))
client.accounts = accounts
print("--------------------------------------------------")
print(f"Running for another {sleep_time} seconds")
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
