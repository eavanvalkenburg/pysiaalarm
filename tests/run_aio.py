#%%
import asyncio
import json
import logging
import os
import time
from importlib import reload

from pysiaalarm.aio import SIAAccount
from pysiaalarm.aio import SIAClient
from pysiaalarm.aio import SIAEvent

reload(logging)

print(os.getcwd())

logging.basicConfig(level=logging.DEBUG)


async def main():
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
    await asyncio.sleep(sleep_time)
    print(f"Client will stop now...")
    print("--------------------------------------------------")
    await client.stop()
    # for ev in events:
    #     print(ev)

    print("--------------------------------------------------")
    print(len(events))
    print(client.counts)
    print("--------------------------------------------------")


asyncio.run(main())
