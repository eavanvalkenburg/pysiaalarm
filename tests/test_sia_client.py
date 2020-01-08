# -*- coding: utf-8 -*-

import time
import pytest
import logging
from pysia.sia_client import SIAClient
from pysia.sia_event import SIAEvent

_LOGGER = logging.getLogger(__name__)

__author__ = "E.A. van Valkenburg"
__copyright__ = "E.A. van Valkenburg"
__license__ = "mit"

class testSIA(object):
    # def test_sia_client(self):
    #     events = []
    #     def func(event: SIAEvent):
    #         events.append(event)
        
    #     client = SIAClient("", 2020, 'acc' 'aaaaaaaaaaaaaaaaaaaaa', func)
    #     time.sleep(60)
    #     assert len(events) > 0
    @pytest.mark.parametrize('line, account, type', [
        ('98100078"*SIA-DCS"5994L0#AAA[5AB718E008C616BF16F6468033A11326B0F7546CAB230910BCA10E4DEBA42283C436E4F8EFF50931070DDE36D5BB5F0C', 'AAA', ''),
        ('2E680078"SIA-DCS"6002L0#AAA[|Nri1/CL501]_14:12:04,09-25-2019', 'AAA', 'Closing Report')
    ])

    def test_event_parsing(self, line, account, type):
        # line = '98100078"*SIA-DCS"5994L0#AAA[5AB718E008C616BF16F6468033A11326B0F7546CAB230910BCA10E4DEBA42283C436E4F8EFF50931070DDE36D5BB5F0C'
        event = SIAEvent(line)
        assert event.account == account
        assert event.type == type

    # def test_event_unencrypted_parsing(self):
    #     line = '2E680078"SIA-DCS"6002L0#AAA[|Nri1/CL501]_14:12:04,09-25-2019'
    #     event = SIAEvent(line)
    #     assert event.account == 'AAA'
    #     assert event.type == 'Closing Report'