# -*- coding: utf-8 -*-
"""This is a class for SIA Events."""
import logging
import re
from datetime import datetime, timedelta

from . import __author__, __copyright__, __license__, __version__
from .sia_const import ALL_CODES
from .sia_errors import EventFormatError

_LOGGER = logging.getLogger(__name__)

main_regex = r"""
(?P<crc>[A-F0-9]{4})
(?P<length>[A-F0-9]{4})\"
(?P<encrypted_flag>[*])?
(?P<message_type>SIA-DCS|NULL)\"
(?P<sequence>[0-9]{4})
(?P<receiver>R[A-F0-9]{1,6})?
(?P<prefix>L[A-F0-9]{1,6})
[#]?(?P<account>[A-F0-9]{3,16})?
[\[]
(?P<rest>.*)
"""
MAIN_MATCHER = re.compile(main_regex, re.X)

content_regex = r"""
[#]?(?P<account>[A-F0-9]{3,16})?
[|]?
[N]?
(?:ti)?(?:(?<=ti)(?P<ti>\d{2}:\d{2}))?\/?
(?:id)?(?:(?<=id)(?P<id>\d*))?\/?
(?:ri)?(?:(?<=ri)(?P<ri>\d*))?\/?
(?P<code>[a-zA-z]{2})?
(?P<message>.*)
[\]][_]?
(?P<timestamp>[0-9:,-]*)?
"""
CONTENT_MATCHER = re.compile(content_regex, re.X)

encr_content_regex = r"""
(?:[^\|\[\]]*)
[|]?
[#]?(?P<account>[a-fA-F0-9]{3,16})?
[|]?
[N]?
(?:ti)?(?:(?<=ti)(?P<ti>\d{2}:\d{2}))?\/?
(?:id)?(?:(?<=id)(?P<id>\d*))?\/?
(?:ri)?(?:(?<=ri)(?P<ri>\d*))?\/?
(?P<code>[a-zA-z]{2})?
(?P<message>.*)
[\]][_]?
(?P<timestamp>[0-9:,-]*)?
"""
ENCR_CONTENT_MATCHER = re.compile(encr_content_regex, re.X)


class SIAEvent:
    """Class for SIAEvents."""

    def __init__(self, line: str):
        """Create a SIA Event from a line.

        Arguments:
            line {str} -- The line to be parsed.

        Raises:
            EventFormatError: If the event is not formatted according to SIA DC09.

        """
        line_match = MAIN_MATCHER.match(line)
        if not line_match:
            raise EventFormatError(
                "No matches found, event was not a SIA Spec event, line was: %s", line
            )
        main_content = line_match.groupdict()

        self.type = None
        self.description = None
        self.concerns = None
        self.timestamp = None
        self._code = None
        self.ti = None
        self.id = None
        self.ri = None
        self.type = None
        self.description = None
        self.concerns = None
        self.code_not_found = True
        self._content = None
        self.message = None
        self.msg_crc = main_content["crc"]
        self.length = main_content["length"]
        self.encrypted = True if main_content["encrypted_flag"] else False
        self.message_type = main_content["message_type"]
        self.sequence = main_content["sequence"]
        self.receiver = main_content["receiver"]
        self.prefix = main_content["prefix"]
        self.account = main_content["account"]
        if self.encrypted:
            self.encrypted_content = main_content["rest"]
        else:
            self.encrypted_content = None
            self.content = main_content["rest"]
        self.full_message = line[8:]
        self.calc_crc = SIAEvent.crc_calc(self.full_message)

    @property
    def content(self):
        """Return the content field."""
        return self._content

    @content.setter
    def content(self, new):
        """Set the content and parse it."""
        self._content = new
        if self.encrypted:
            matches = ENCR_CONTENT_MATCHER.match(self._content)
        else:
            matches = CONTENT_MATCHER.match(self._content)
        if not matches:
            raise EventFormatError(
                "Parse content: no matches found in %s", self._content
            )
        content = matches.groupdict()
        if not self.account:
            self.account = content["account"]
        self.ti = content["ti"]
        self.id = content["id"]
        self.ri = content["ri"]  # renamed from zone
        self.code = content["code"]
        self.message = content["message"]
        self.timestamp = (
            datetime.strptime(content["timestamp"], "%H:%M:%S,%m-%d-%Y")
            if content["timestamp"]
            else None
        )
        if self.message_type == "NULL" and not self.code:
            self.code = "RP"
            self.ri = 0

    @property
    def code(self):
        """Return the code field."""
        return self._code

    @code.setter
    def code(self, new):
        """Set self.code and get the related fields for a code."""
        self._code = new
        full = ALL_CODES.get(self._code, None)
        if full:
            self.type = full.get("type")
            self.description = full.get("description")
            self.concerns = full.get("concerns")
            self.code_not_found = False
        else:
            self.code_not_found = True

    def valid_timestamp(self, allowed_timeband) -> bool:
        """Check if the timestamp is within bounds."""
        if not allowed_timeband[0]:
            return True
        if self.timestamp:
            current_time = datetime.utcnow()
            current_min = current_time - timedelta(seconds=allowed_timeband[0])
            current_plus = current_time + timedelta(seconds=allowed_timeband[1])
            return current_min <= self.timestamp <= current_plus
        else:
            return True

    @classmethod
    def crc_calc(cls, msg: str) -> str:
        """Calculate the CRC of the events."""
        crc = 0
        for letter in str.encode(msg):
            temp = letter
            for _ in range(0, 8):
                temp ^= crc & 1
                crc >>= 1
                if (temp & 1) != 0:
                    crc ^= 0xA001
                temp >>= 1
        return ("%x" % crc).upper().zfill(4)

    @property
    def valid_message(self) -> bool:
        """Check the validity of the message by comparing the sent CRC with the calculated CRC."""
        return self.msg_crc == self.calc_crc

    @property
    def valid_length(self) -> bool:
        """Check if the length of the message is the same in the message and supplied. Will not throw an error if not correct."""
        return int(self.length) == int(str(len(self.full_message)), 16)

    @property
    def sia_string(self) -> str:
        """Create a string with the SIA codes and some other fields."""
        return f"Code: {self.code}, Type: {self.type}, \
            Description: {self.description}"

    def __str__(self):
        """Return a string of a event."""
        return f"\
Content: {self.content}, \
Zone (ri): {self.ri}, \
Code: {self.code}, \
Message: {self.message if self.message else ''}, \
Concerns: {self.concerns}, \
Type: {self.type}, \
Description: {self.description}, \
Account: {self.account}, \
Receiver: {self.receiver}, \
Prefix: {self.prefix}, \
Timestamp: {self.timestamp}, \
Length: {self.length}, \
Sequence: {self.sequence}, \
CRC: {self.msg_crc}, \
Calc CRC: {self.calc_crc}, \
Message type: {self.type}, \
Encrypted Content: {self.encrypted_content}, \
Full Message: {self.full_message}."
