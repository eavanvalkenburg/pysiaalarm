# -*- coding: utf-8 -*-

import time
import pytest
from pysia.sia_client import SIAClient
from pysia.sia_event import SIAEvent

__author__ = "E.A. van Valkenburg"
__copyright__ = "E.A. van Valkenburg"
__license__ = "mit"

# def test_sia_client():
#     events = []
#     def func(event: SIAEvent):
#         events.append(event)
    
#     client = SIAClient("", 2020, 'acc' 'aaaaaaaaaaaaaaaaaaaaa', func)
#     time.sleep(60)
#     assert len(events) > 0

def test_event_parsing():
    line = r'2E680078"SIA-DCS"6002L0#acct[|Nri1/CL501]_14:12:04,09-25-2019'
    event = SIAEvent(line)
    print(event)