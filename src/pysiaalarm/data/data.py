"""Data related utils for pysiaalarm."""
import json
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from typing import Dict, Optional

import pkg_resources

FILE_SIA_CODES = "sia_codes.json"
FILE_XDATA = "xdata.json"
FILE_ADM_MAPPING = "adm_mapping.json"


@dataclass_json
@dataclass
class SIACode:
    """Class for SIACodes."""

    code: str
    type: str
    description: str
    concerns: str


@dataclass_json
@dataclass
class SIAXData:
    """Class for Xdata."""

    identifier: str
    name: str
    description: str
    length: int
    characters: str
    value: Optional[str] = None


def _load_data(file: str) -> dict:
    """Load the one of the data json files."""
    stream = pkg_resources.resource_stream(__name__, file)
    return json.load(stream)


def _load_sia_codes() -> Dict[str, SIACode]:
    """Alias for loading sia codes file."""
    data = _load_data(FILE_SIA_CODES)
    return {key: SIACode(**value) for (key, value) in data.items()}


def _load_xdata() -> Dict[str, SIAXData]:
    """Alias for loading xdata file."""
    data = _load_data(FILE_XDATA)
    return {key: SIAXData(**value) for (key, value) in data.items()}


def _load_adm_mapping() -> Dict[str, Dict[str, str]]:
    """Alias for loading adm mapping file."""
    return _load_data(FILE_ADM_MAPPING)
