from pysiaalarm import (
    InvalidAccountFormatError,
    InvalidAccountLengthError,
    InvalidKeyFormatError,
    InvalidKeyLengthError,
    Protocol,
)
from pysiaalarm.sia_errors import EventFormatError
from pysiaalarm.sia_account import SIAResponseType
from tests.test_utils import ACCOUNT, KEY


def encrypted_encrypted():
    """Return a key for a encrypted test."""
    return KEY


def encrypted_unencrypted():
    """Return None for a unencrypted test."""
    return None


def proto_tcp():
    """Return TCP protocol."""
    return Protocol.TCP


def proto_udp():
    """Return UDP protocol."""
    return Protocol.UDP


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
    """Test class for Message type SIA-DCS"""
    return "SIA-DCS"


def msg_null():
    """Test class for Message type SIA-DCS"""
    return "NULL"


class EventParsing:
    """Test cases for event parsing.

    Emits these fields: "line, account_id, type, code, error"

    """

    def case_dc04(self):
        """Test case DC04 format - NOT SUPPORTED so throws an error."""
        return (
            r'<x0A>CE110032"SIA-DCS"9876R579BDFL789ABC#12345A[#12345A|NFA129]<x0D>',
            "12345A",
            None,
            None,
            EventFormatError,
        )

    def case_dc05(self):
        """Test case DC05 format with ADM-CID - NOT SUPPORTED so throws an error."""
        return (
            r'<x0A>87CD0037"ADM-CID"9876R579BDFL789ABC#12345A[#12345A|1110 00 129]<x0D>',
            "12345A",
            None,
            None,
            EventFormatError,
        )

    def case_xdata(self):
        """Input a closing report event in SIA DC-09 with xdata"""
        return (
            r'E5D50078"SIA-DCS"6002L0#AAA[|Nri1/CL501][M0026B9E4268B]_14:12:04,09-25-2019',
            "AAA",
            "Closing Report",
            "CL",
            None,
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
        )

    def case_cl(self):
        """Input a closing report event in SIA DC-09."""
        return (
            r'E5D50078"SIA-DCS"6002L0#AAA[|Nri1/CL501]_14:12:04,09-25-2019',
            "AAA",
            "Closing Report",
            "CL",
            None,
        )

    def case_op(self):
        """Input a opening report event."""
        return (
            r'90820051"SIA-DCS"4738R0001L0001[#006969|Nri04/OP001NM]',
            "006969",
            "Opening Report",
            "OP",
            None,
        )

    def case_null(self):
        """Input a encrypted null event."""
        return (
            r'76D80055"*NULL"0000R0L0#AAAB[B4BC8B40D0E6D959D6BEA78E88CC0B2155741A3C44FBB96D476A3E557CAD64D9',
            "AAAB",
            None,
            None,
            None,
        )

    def case_wa(self):
        """Input a water alarm event."""
        return (
            r'C4160279"SIA-DCS"5268L0#AAA[Nri1/WA000]_08:40:47,07-08-2020',
            "AAA",
            "Water Alarm",
            "WA",
            None,
        )

    def case_eventformaterror(self):
        """Input a event format error event."""
        return (r"this is not a parsable event", None, None, None, EventFormatError)


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


class ParseAndCheckEvent:
    """Test cases for parse and check event function.

    Emits these fields: "account_id, code, msg_type, alter_key, wrong_event, response"

    """

    def case_rp(self):
        """Test unencrypted parsing of RP event."""
        return ("RP", False, False, SIAResponseType.ACK)

    def case_wa(self):
        """Test unencrypted parsing of WA event."""
        return ("WA", False, False, SIAResponseType.ACK)

    def case_altered_key(self):
        """Test encrypted parsing of RP event.

        Altered key means the event can be parsed as a SIA Event but the content cannot be decrypted.

        """
        return ("RP", True, False, SIAResponseType.NAK)

    def case_wrong_event(self):
        """Test encrypted parsing of RP event."""
        return ("RP", False, True, SIAResponseType.NAK)
