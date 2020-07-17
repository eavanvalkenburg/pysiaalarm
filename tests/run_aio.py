#%%
import asyncio
import json
import logging
import os
import random
import time

from pysiaalarm.aio import SIAAccount, SIAClient, SIAEvent

logging.basicConfig(level=logging.DEBUG)


async def main():
    events = []

    async def func(event: SIAEvent):
        # if random.random() > 0.8:
        #     raise ValueError
        events.append(event)

    with open("local_config.json", "r") as f:
        config = json.load(f)
    account = [SIAAccount(config["account_id"], config["key"])]
    async with SIAClient(
        config["host"], config["port"], account, function=func
    ) as client:
        # client.start()
        sleep_time = 12000
        print("--------------------------------------------------")

        # await asyncio.sleep(20)
        # print(f"Client started... adding extra account")
        # accounts = client.accounts
        # accounts.append(SIAAccount("FFFFFFFFF", config["key"]))
        # client.accounts = accounts
        # print("--------------------------------------------------")

        print(f"Running for another {sleep_time} seconds")
        await asyncio.sleep(sleep_time / 2)
        print(client.counts)
        await asyncio.sleep(sleep_time / 2)
        print("--------------------------------------------------")
        # for ev in events:
        #     print(ev)
        print("--------------------------------------------------")
        print(len(events))
        print(client.counts)
        print("--------------------------------------------------")


asyncio.run(main())
