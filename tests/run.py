#%%
import json
import logging
import os
import time
from importlib import reload

from pysiaalarm import dist_name
from pysiaalarm.sia_account import SIAAccount
from pysiaalarm.sia_client import SIAClient
from pysiaalarm.sia_event import SIAEvent

reload(logging)

print(os.getcwd())

logging.basicConfig(level=logging.DEBUG)

#%%
events = []


def func(event: SIAEvent):
    logging.info(event)
    events.append(event)


with open("local_config.json", "r") as f:
    config = json.load(f)
#%%
client = SIAClient(
    config["host"],
    config["port"],
    [SIAAccount(config["account_id"], config["key"])],
    function=func,
)

#%%
client.start()
#%%
time.sleep(3600)
#%%
client.stop()
#%%
print("--------------------------------------------------")
for ev in events:
    print(ev)

# %%
print("--------------------------------------------------")
print(len(events))
print("--------------------------------------------------")
# %%
