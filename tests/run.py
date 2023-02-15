import json
import logging
import time

from pysiaalarm import SIAAccount, SIAClient, SIAEvent
from pysiaalarm import CommunicationsProtocol

logging.basicConfig(level=logging.DEBUG)

events = []


def func(event: SIAEvent):
    events.append(event)


with open("local_config.json", "r") as f:
    config = json.load(f)
print("Config: ", config)
account = [SIAAccount(config["account_id"], config["key"])]
sleep_time = 1200
with SIAClient(config["host"], config["port"], account, function=func, 
               protocol = CommunicationsProtocol.TCP | CommunicationsProtocol.OH) as client:
    time.sleep(sleep_time)
    counts = client.counts

# for ev in events:
#     print(ev)

print("--------------------------------------------------")
print("Number of events: ", len(events))
print("Counts: ", counts)
print("--------------------------------------------------")
