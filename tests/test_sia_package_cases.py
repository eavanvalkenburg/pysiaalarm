from pysiaalarm import (
    InvalidAccountFormatError,
    InvalidAccountLengthError,
    InvalidKeyFormatError,
    InvalidKeyLengthError,
    SIAAccount,
    SIAClient,
    SIAEvent,
)
from pysiaalarm.sia_errors import EventFormatError
from pysiaalarm.sia_account import SIAResponseType
from tests.test_utils import ACCOUNT, KEY, HOST


class EventParsing:
    """Test cases for event parsing.

    Emits these fields: "line, account_id, type, code, error"

    """

    def case_encrypted(self):
        """Input a encrypted line."""
        return (
            r'60AB0078"*SIA-DCS"5994L0#AAA[5AB718E008C616BF16F6468033A11326B0F7546CAB230910BCA10E4DEBA42283C436E4F8EFF50931070DDE36D5BB5F0C',
            "AAA",
            None,
            None,
            Exception,
        )

    def case_cl(self):
        """Input a closing report event."""
        return (
            r'E5D50078"SIA-DCS"6002L0#AAA[|Nri1/CL501]_14:12:04,09-25-2019',
            "AAA",
            "Closing Report",
            "CL",
            Exception,
        )

    def case_op(self):
        """Input a opening report event."""
        return (
            r'90820051"SIA-DCS"4738R0001L0001[#006969|Nri04/OP001NM]',
            "006969",
            "Opening Report",
            "OP",
            Exception,
        )

    def case_null(self):
        """Input a encrypted null event."""
        return (
            r'76D80055"*NULL"0000R0L0#AAAB[B4BC8B40D0E6D959D6BEA78E88CC0B2155741A3C44FBB96D476A3E557CAD64D9',
            "AAAB",
            None,
            None,
            Exception,
        )

    def case_wa(self):
        """Input a water alarm event."""
        return (
            r'C4160279"SIA-DCS"5268L0#AAA[Nri1/WA000]_08:40:47,07-08-2020',
            "AAA",
            "Water Alarm",
            "WA",
            Exception,
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


class TestClient:
    """Test class for client.

    Emits these fields: "config, fail_func"

    """

    def case_unencrypted_config_good_func(self):
        """Test unencrypted config and a good func."""
        return ({"host": HOST, "account_id": ACCOUNT, "key": ""}, False)

    def case_encrypted_config_good_func(self):
        """Test encrypted config and a good func."""
        return ({"host": HOST, "account_id": ACCOUNT, "key": KEY}, False)

    def case_unencrypted_config_bad_func(self):
        """Test unencrypted config and a bad func."""
        return ({"host": HOST, "account_id": ACCOUNT, "key": ""}, True)

    def case_encrypted_config_bad_func(self):
        """Test encrypted config and a bad func."""
        return ({"host": HOST, "account_id": ACCOUNT, "key": KEY}, True)


class ParseAndCheckEvent:
    """Test cases for parse and check event function.

    Emits these fields: "account_id, key, code, msg_type, alter_key, wrong_event, response"

    """

    def case_unencrypted_rp(self):
        """Test unencrypted parsing of RP event."""
        return (ACCOUNT, None, "RP", "SIA-DCS", False, False, SIAResponseType.ACK)

    def case_unencrypted_wa(self):
        """Test unencrypted parsing of WA event."""
        return (ACCOUNT, None, "WA", "SIA-DCS", False, False, SIAResponseType.ACK)

    def case_encrypted_rp(self):
        """Test encrypted parsing of RP event."""
        return (ACCOUNT, KEY, "RP", "SIA-DCS", False, False, SIAResponseType.ACK)

    def case_unencrypted_rp_null(self):
        """Test encrypted parsing of RP event."""
        return (ACCOUNT, None, "RP", "NULL", False, False, SIAResponseType.ACK)

    def case_encrypted_rp_null(self):
        """Test encrypted parsing of RP event."""
        return (ACCOUNT, KEY, "RP", "NULL", False, False, SIAResponseType.ACK)

    def case_altered_key(self):
        """Test encrypted parsing of RP event.

        Altered key means the event can be parsed as a SIA Event but the content cannot be decrypted.

        """
        return (ACCOUNT, KEY, "RP", "NULL", True, False, SIAResponseType.NAK)

    def case_wrong_event(self):
        """Test encrypted parsing of RP event."""
        return (ACCOUNT, KEY, "RP", "NULL", False, True, SIAResponseType.NAK)


class FuncErrors:
    """Test class for function errors.

    Emits these fields: "async_client, async_func, error_type"

    """

    def case_sync_sync_success(self):
        """Test case for sync client and sync func."""
        return (False, False, None)

    def case_async_async_success(self):
        """Test case for async client and async func."""
        return (True, True, None)

    def case_sync_async_fail(self):
        """Test case for sync client and async func."""
        return (False, True, TypeError)

    def case_async_sync_fail(self):
        """Test case for async client and sync func."""
        return (True, False, TypeError)
