# -*- coding: utf-8 -*-
"""This is a class for SIA Events."""
import logging
import re
from datetime import datetime, timedelta

from pysiaalarm import __version__
from pysiaalarm.sia_const import ALL_CODES
from pysiaalarm.sia_errors import CRCMismatchError, EventFormatError

__author__ = "E.A. van Valkenburg"
__copyright__ = "E.A. van Valkenburg"
__license__ = "mit"
__version__ = __version__

logging.getLogger(__name__)


class SIAEvent:
    """Class for SIA Events."""

    def __init__(self, line: str):
        """Create a SIA Event from a line.

        Arguments:
            line {str} -- The line to be parsed.

        Raises:
            EventFormatError: If the event is not formatted according to SIA DC09.
            CRCMismatchError: Error when there is a mismatch in CRC Codes.

        """
        regex = r"([A-F0-9]{4})([A-F0-9]{4})(\"(SIA-DCS|\*SIA-DCS)\"([0-9]{4})(R[A-F0-9]{1,6})?(L[A-F0-9]{1,6})#([A-F0-9]{3,16})\[([A-F0-9]*)?(.*Nri(\d*)/([a-zA-z]{2})(.*)]_([0-9:,-]*))?)"
        matches = re.findall(regex, line)
        # check if there is at least one match
        if not matches:
            raise EventFormatError(
                "No matches found, event was not a SIA Spec event, line was: %s", line
            )
        # logging.debug(matches)
        self.msg_crc, self.length, self.full_message, self.message_type, self.sequence, self.receiver, self.prefix, self.account, self.encrypted_content, self.content, self.zone, self.code, self.message, self.timestamp = matches[
            0
        ]
        self.type = ""
        self.description = ""
        self.concerns = ""
        self.calc_crc = SIAEvent.crc_calc(self.full_message)
        self._parse_timestamp()
        if not self.valid_message:
            raise CRCMismatchError("Event %s had a mismatched CRC", self)
        if self.code:
            self._add_sia()

    def _add_sia(self):
        """Find the sia codes based on self.code."""
        full = ALL_CODES.get(self.code, None)
        if full:
            self.type = full.get("type")
            self.description = full.get("description")
            self.concerns = full.get("concerns")
            self.code_not_found = False
        else:
            self.code_not_found = True

    def parse_decrypted(self):
        """When the content was decrypted, update the fields contained within."""
        regex = r".*Nri(\d*)/([a-zA-z]{2})(.*)]_([0-9:,-]*)"
        matches = re.findall(regex, self.content)
        if not matches:
            raise EventFormatError(
                "Parse Decrypted: no matches found in %s", self.content
            )
        self.zone, self.code, self.message, self.timestamp = matches[0]
        self._parse_timestamp()
        if self.code:
            self._add_sia()

    def _parse_timestamp(self):
        """Parse the timestamp."""
        if self.timestamp:
            self.timestamp = datetime.strptime(self.timestamp, "%H:%M:%S,%m-%d-%Y")

    def valid_timestamp(self, allowed_timeband) -> bool:
        """Check if the timestamp is within bounds."""
        if self.timestamp:
            current_time = datetime.utcnow()
            current_min40 = current_time - timedelta(seconds=allowed_timeband[0])
            current_plus20 = current_time + timedelta(seconds=allowed_timeband[1])
            logging.info("Comparing between %s and %s", current_min40, current_plus20)
            return current_min40 <= self.timestamp <= current_plus20
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
            Description: {self.description}, Concerns: {self.concerns}"

    def __str__(self):
        """Return a string of a event."""
        return f"\
Content: {self.content}, \
Zone: {self.zone}, \
Code: {self.code}, \
Message: {self.message}, \
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
Message type: {self.message_type}, \
Encrypted Content: {self.encrypted_content}, \
Full Message: {self.full_message}."
