from typing import TypedDict


class XDataEntry(TypedDict):
    characters: str
    description: str
    identifier: str
    length: int
    name: str


XDATA: dict[str, XDataEntry] = {
    "A": {
        "characters": "ASCII",
        "description": "A hash of the message that allows the message to be "
        "authenticated.",
        "identifier": "A",
        "length": 12,
        "name": "Authentication Hash",
    },
    "C": {
        "characters": "ASCII",
        "description": "An identifier for the number of communication paths "
        "and link supervision category",
        "identifier": "C",
        "length": 64,
        "name": "Supervision Category",
    },
    "H": {
        "characters": "ASCII",
        "description": "Time that event occurred (may be different than "
        "message time stamp)",
        "identifier": "H",
        "length": 21,
        "name": "Time of Occurence",
    },
    "I": {
        "characters": "Win1252",
        "description": "Alarm text which may be a description of the event or "
        "a comment regarding the event.",
        "identifier": "I",
        "length": 256,
        "name": "Alarm Text",
    },
    "J": {
        "characters": "ASCII",
        "description": "Manufacturer specific identifier for the path that "
        "was used for the communication",
        "identifier": "J",
        "length": 1,
        "name": "Network Path",
    },
    "K": {
        "characters": "ASCII",
        "description": "Key exchange request from CSR to PE (up to 256 bits)",
        "identifier": "K",
        "length": 64,
        "name": "Encryption Key",
    },
    "L": {
        "characters": "Win1252",
        "description": "Location of event on site",
        "identifier": "L",
        "length": 256,
        "name": "Location",
    },
    "M": {
        "characters": "ASCII",
        "description": "MAC address of the PE.",
        "identifier": "M",
        "length": 12,
        "name": "MAC Address",
    },
    "N": {
        "characters": "ASCII",
        "description": "Hardware network address associated with the "
        "communication on path used.",
        "identifier": "N",
        "length": 128,
        "name": "Network Address",
    },
    "O": {
        "characters": "Win1252",
        "description": "Building name.",
        "identifier": "O",
        "length": 256,
        "name": "Building Name",
    },
    "P": {
        "characters": "Win1252",
        "description": "contains a message used to support programming or "
        "other interactive operations with the receiver",
        "identifier": "P",
        "length": 256,
        "name": "Authentication Hash",
    },
    "R": {
        "characters": "Win1252",
        "description": "Room of the event.",
        "identifier": "R",
        "length": 256,
        "name": "Room",
    },
    "S": {
        "characters": "Win1252",
        "description": "Site name describing the premises.",
        "identifier": "S",
        "length": 256,
        "name": "Site name",
    },
    "T": {
        "characters": "ASCII",
        "description": "Trigger for the event.",
        "identifier": "T",
        "length": 1,
        "name": "Alarm Trigger",
    },
    "V": {
        "characters": "Win1252",
        "description": "information about audio or video information that may "
        "be associated with the event report.",
        "identifier": "V",
        "length": 256,
        "name": "Verification",
    },
    "X": {
        "characters": "ASCII",
        "description": "Location of event, longitude.",
        "identifier": "X",
        "length": 12,
        "name": "Longitude",
    },
    "Y": {
        "characters": "ASCII",
        "description": "Location of event, latitude.",
        "identifier": "Y",
        "length": 12,
        "name": "Latitude",
    },
    "Z": {
        "characters": "ASCII",
        "description": "Location of event, altitude.",
        "identifier": "Z",
        "length": 12,
        "name": "Altitude",
    },
}
