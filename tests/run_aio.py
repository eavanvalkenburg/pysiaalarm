#%%
import asyncio
import json
import logging
import os
import time

from pysiaalarm.aio import SIAAccount
from pysiaalarm.aio import SIAClient
from pysiaalarm.aio import SIAEvent

logging.basicConfig(level=logging.DEBUG)


async def main():
    events = []

    async def func(event: SIAEvent):
        events.append(event)

    with open("unencrypted_config.json", "r") as f:
        config = json.load(f)
    account = [SIAAccount(config["account_id"], config["key"])]
    client = SIAClient(config["host"], config["port"], account, function=func)
    client.start()
    sleep_time = 120
    print("--------------------------------------------------")

    await asyncio.sleep(20)
    print(f"Client started... adding extra account")
    accounts = client.accounts
    accounts.append(SIAAccount("FFFFFFFFF", config["key"]))
    client.accounts = accounts
    print("--------------------------------------------------")

    print(f"Running for another {sleep_time} seconds")
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
