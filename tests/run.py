#%%
import time
import logging
import json
from pysia.sia_client import SIAClient
from pysia.sia_event import SIAEvent
from pysia import dist_name

logging.basicConfig(level=logging.DEBUG)
logging.getLogger(dist_name)
# logging.setLevel(logging.DEBUG)

#%%
events = []


def func(event: SIAEvent):
    logging.info(event)
    events.append(event)

with open("local_config.json", 'r') as f:
    config = json.load(f)
#%%
client = SIAClient(
    **config, function=func
)
#%%
client.start()
#%%
time.sleep(60)
#%%
client.stop()
#%%
for ev in events:
    print(ev)

# %%
