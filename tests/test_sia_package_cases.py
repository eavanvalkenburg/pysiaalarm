"""Test cases."""
from pytest_cases import case

from pysiaalarm import (
    InvalidAccountFormatError,
    InvalidAccountLengthError,
    InvalidKeyFormatError,
    InvalidKeyLengthError,
    CommunicationsProtocol,
    SIAAccount,
    SIAEvent,
)
from pysiaalarm.errors import EventFormatError
from pysiaalarm.utils import ResponseType
from pysiaalarm.const import (
    COUNTER_ACCOUNT,
    COUNTER_CRC,
    COUNTER_CODE,
    COUNTER_FORMAT,
    COUNTER_TIMESTAMP,
)
from tests.test_utils import ACCOUNT, KEY


def encrypted_encrypted():
    """Return a key for a encrypted test."""
    return KEY


def encrypted_unencrypted():
    """Return None for a unencrypted test."""
    return None


def proto_tcp():
    """Return TCP protocol."""
    return CommunicationsProtocol.TCP


def proto_udp():
    """Return UDP protocol."""
    return CommunicationsProtocol.UDP


def sync_sync():
    """Return True for running a sync/threaded test."""
    return True


def sync_async():
    """Return False for running a async test."""
    return False


def handler_good():
    """Return True for a good event handler."""
    return True


def handler_bad():
    """Return False for a bad event handler."""
    return False


def msg_siadcs():
    """Test class for Message type SIA-DCS."""
    return "SIA-DCS"


def msg_admcid():
    """Test class for Message type ADM-CID."""
    return "ADM-CID"


def msg_null():
    """Test class for Message type SIA-DCS."""
    return "NULL"


def fault_none():
    """Test class for no fault in the message."""
    return None


def fault_code():
    """Test class for a code fault in the message."""
    return COUNTER_CODE


def fault_crc():
    """Test class for a crc fault in the message."""
    return COUNTER_CRC


def fault_format():
    """Test class for a format fault in the message."""
    return COUNTER_FORMAT


def fault_account():
    """Test class for a account fault in the message."""
    return COUNTER_ACCOUNT


def fault_timestamp():
    """Test class for a timestamp fault in the message."""
    return COUNTER_TIMESTAMP


class EventParsing:
    """Test cases for event parsing.

    Emits these fields: "line, account_id, type, code, error, extended_data_flag"

    """

    def case_bug(self):
        """Test case from #11."""
        return (
            r'9618004D"SIA-DCS"7960L0#123456[#123456|Nri1CL0^VX FRONTE ^]_22:40:48,04-11-2021',
            "123456",
            "Closing Report",
            "CL",
            None,
            False,
        )

    def case_bug2(self):
        """Test case from SIA #42."""
        return (
            r'5670004D"SIA-DCS"8070L0#123456[#123456|Nri0KR1^TAST. 001 ^]_13:49:12,04-13-2021',
            "123456",
            "Heat Restoral",
            "KR",
            None,
            False,
        )

    def case_dc04(self):
        """Test case DC04 format - NOT SUPPORTED so throws an error."""
        return (
            r'<x0A>CE110032"SIA-DCS"9876R579BDFL789ABC#12345A[#12345A|NFA129]_14:12:04,09-25-201',
            "12345A",
            None,
            None,
            EventFormatError,
            False,
        )

    def case_adm_cid(self):
        """Test case ADM-CID format."""
        return (
            r'87CD0037"ADM-CID"9876R579BDFL789ABC#12345A[#12345A|1110 00 129]_14:12:04,09-25-201',
            "12345A",
            "Fire Alarm",
            "FA",
            None,
            False,
        )

    def case_xdata_M(self):
        """Input a closing report event in SIA DC-09 with M xdata."""
        return (
            r'E5D50078"SIA-DCS"6002L0#AAA[|Nri1/CL501][M0026B9E4268B]_14:12:04,09-25-2019',
            "AAA",
            "Closing Report",
            "CL",
            None,
            True,
        )

    def case_xdata_K(self):
        """Input a closing report event in SIA DC-09 with K xdata."""
        return (
            rf'02310052"SIA-DCS"6002L0#{ACCOUNT}[|Nri1/RP000][KAAAAAAAAAAAAAAAA]_14:12:04,09-25-2019',
            ACCOUNT,
            "Automatic Test",
            "RP",
            None,
            True,
        )

    # TODO: add tests for different SIA versions (DC-04, DC09, DC09X)
    def case_encrypted(self):
        """Input a encrypted line."""
        return (
            r'60AB0078"*SIA-DCS"5994L0#AAA[5AB718E008C616BF16F6468033A11326B0F7546CAB230910BCA10E4DEBA42283C436E4F8EFF50931070DDE36D5BB5F0C',
            "AAA",
            None,
            None,
            None,
            False,
        )

    def case_oh(self):
        """Input a OH event."""
        return (
            r"SR0001L0001    006969XX    [ID00000000]",
            "006969XX",
            "Automatic Test",
            "RP",
            None,
            False,
        )

    def case_cl(self):
        """Input a closing report event in SIA DC-09."""
        return (
            r'E5D50078"SIA-DCS"6002L0#AAA[|Nri1/CL501]_14:12:04,09-25-2019',
            "AAA",
            "Closing Report",
            "CL",
            None,
            False,
        )

    def case_op(self):
        """Input a opening report event."""
        return (
            r'90820051"SIA-DCS"4738R0001L0001[#006969|Nri04/OP001NM]',
            "006969",
            "Opening Report",
            "OP",
            None,
            False,
        )

    def case_null(self):
        """Input a encrypted null event."""
        return (
            r'76D80055"*NULL"0000R0L0#AAAB[B4BC8B40D0E6D959D6BEA78E88CC0B2155741A3C44FBB96D476A3E557CAD64D9',
            "AAAB",
            None,
            None,
            None,
            False,
        )

    def case_wa(self):
        """Input a water alarm event."""
        return (
            r'C4160279"SIA-DCS"5268L0#AAA[Nri1/WA000]_08:40:47,07-08-2020',
            "AAA",
            "Water Alarm",
            "WA",
            None,
            False,
        )

    def case_eventformaterror(self):
        """Input a event format error event."""
        return (
            r"this is not a parsable event",
            None,
            None,
            None,
            EventFormatError,
            False,
        )


class AccountSetup:
    """Test cases for key and account errors.

    Emits these fields: "key, account_id, error"

    """

    def case_InvalidKeyFormat(self):
        """Test invalid key format."""
        return ("ZZZZZZZZZZZZZZZZ", ACCOUNT, InvalidKeyFormatError)

    def case_InvalidKeyLength_15(self):
        """Test invalid key length at 15."""
        return ("158888888888888", ACCOUNT, InvalidKeyLengthError)

    def case_correct_16(self):
        """Test correct key at 16."""
        return ("1688888888888888", ACCOUNT, None)

    def case_InvalidKeyLength_23(self):
        """Test invalid key length at 23."""
        return (
            "23888888888888888888888",
            ACCOUNT,
            InvalidKeyLengthError,
        )

    def case_correct_24(self):
        """Test correct key at 24."""
        return ("248888888888888888888888", ACCOUNT, None)

    def case_InvalidKeyLength_31(self):
        """Test invalid key length at 31."""
        return (
            "3188888888888888888888888888888",
            ACCOUNT,
            InvalidKeyLengthError,
        )

    def case_correct_32(self):
        """Test correct at 32."""
        return ("32888888888888888888888888888888", ACCOUNT, None)

    def case_InvalidAccountLength(self):
        """Test invalid account length at 2."""
        return (KEY, "22", InvalidAccountLengthError)

    def case_InvalidAccountFormat(self):
        """Test invalid account format."""
        return (KEY, "ZZZ", InvalidAccountFormatError)

    def case_InvalidAccountLength_NoKey(self):
        """Test invalid account length at 2."""
        return (None, "22", InvalidAccountLengthError)

    def case_InvalidAccountFormat_NoKey(self):
        """Test invalid account format."""
        return (None, "ZZZ", InvalidAccountFormatError)


class ParseAndCheckEvent:
    """Test cases for parse and check event function.

    Emits these fields: "code, alter_key, wrong_event, response"

    """

    def case_rp(self):
        """Test unencrypted parsing of RP event."""
        return ("RP", False, False, ResponseType.ACK)

    def case_wa(self):
        """Test unencrypted parsing of WA event."""
        return ("WA", False, False, ResponseType.ACK)

    def case_altered_key(self):
        """Test encrypted parsing of RP event.

        Altered key means the event can be parsed as a SIA Event but the content cannot be decrypted.

        """
        return ("RP", True, False, ResponseType.NAK)

    def case_wrong_event(self):
        """Test encrypted parsing of RP event."""
        return ("RP", False, True, ResponseType.NAK)

    @case(tags="SIA-DCS")
    def case_non_existent_code(self):
        """Test parsing for non existing code."""
        return ("ZX", False, False, ResponseType.DUH)


class ToFromDict:
    """Test the event serialization to and from dict.

    Emits the class and a dict of that class.

    """

    def case_sia_event(self):
        """Test event from dict."""
        d_ev = {
            "full_message": '"SIA-DCS"5268L0#AAA[Nri1/WA000]_08:40:47,07-08-2020',
            "msg_crc": "C416",
            "length": "0279",
            "encrypted": False,
            "message_type": "SIA-DCS",
            "receiver": None,
            "line": "L0",
            "account": "AAA",
            "sequence": "5268",
            "content": "Nri1/WA000]_08:40:47,07-08-2020",
            "encrypted_content": None,
            "ti": None,
            "id": None,
            "ri": "1",
            "code": "WA",
            "message": "000",
            "x_data": None,
            "timestamp": 1594197647.0,
            "event_qualifier": None,
            "event_type": None,
            "partition": None,
            "calc_crc": "E9A4",
            "extended_data": None,
            "sia_account": None,
            "sia_code": {
                "code": "WA",
                "type": "Water Alarm",
                "description": "Water detected at protected premises",
                "concerns": "Zone or point",
            },
        }
        return SIAEvent, d_ev, False

    def case_sia_event_with_account(self):
        """Test event from dict."""
        d_ev = {
            "full_message": '"SIA-DCS"5268L0#AAA[Nri1/WA000]_08:40:47,07-08-2020',
            "msg_crc": "C416",
            "length": "0279",
            "encrypted": False,
            "message_type": "SIA-DCS",
            "receiver": None,
            "line": "L0",
            "account": "AAA",
            "sequence": "5268",
            "content": "Nri1/WA000]_08:40:47,07-08-2020",
            "encrypted_content": None,
            "ti": None,
            "id": None,
            "ri": "1",
            "code": "WA",
            "message": "000",
            "x_data": None,
            "timestamp": 1594197647.0,
            "event_qualifier": None,
            "event_type": None,
            "partition": None,
            "calc_crc": "E9A4",
            "extended_data": None,
            "sia_account": {"account_id": ACCOUNT, "key": KEY},
            "sia_code": {
                "code": "WA",
                "type": "Water Alarm",
                "description": "Water detected at protected premises",
                "concerns": "Zone or point",
            },
        }
        return SIAEvent, d_ev, False

    def case_sia_event_with_account_clear(self):
        """Test event from dict."""
        d_ev = {
            "full_message": '"SIA-DCS"5268L0#AAA[Nri1/WA000]_08:40:47,07-08-2020',
            "msg_crc": "C416",
            "length": "0279",
            "encrypted": False,
            "message_type": "SIA-DCS",
            "receiver": None,
            "line": "L0",
            "account": "AAA",
            "sequence": "5268",
            "content": "Nri1/WA000]_08:40:47,07-08-2020",
            "encrypted_content": None,
            "ti": None,
            "id": None,
            "ri": "1",
            "code": "WA",
            "message": "000",
            "x_data": None,
            "timestamp": 1594197647.0,
            "event_qualifier": None,
            "event_type": None,
            "partition": None,
            "calc_crc": "E9A4",
            "extended_data": None,
            "sia_account": {"account_id": ACCOUNT, "key": KEY},
            "sia_code": {
                "code": "WA",
                "type": "Water Alarm",
                "description": "Water detected at protected premises",
                "concerns": "Zone or point",
            },
        }
        return SIAEvent, d_ev, True

    def case_sia_account(self):
        """Test account to and from dict."""
        return SIAAccount, {"account_id": ACCOUNT, "key": KEY}, False
