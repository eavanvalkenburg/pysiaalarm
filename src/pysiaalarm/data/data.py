"""Data related utils for pysiaalarm."""
from __future__ import annotations

import json
from dataclasses import dataclass

import pkg_resources

FILE_SIA_CODES = "sia_codes.json"
FILE_XDATA = "xdata.json"
FILE_ADM_MAPPING = "adm_mapping.json"


@dataclass
class SIACode:
    """Class for SIACodes."""

    code: str
    type: str
    description: str
    concerns: str


@dataclass
class SIAXData:
    """Class for Xdata."""

    identifier: str
    name: str
    description: str
    length: int
    characters: str
    value: str | None = None


def _load_data(file: str) -> dict:
    """Load the one of the data json files."""
    stream = pkg_resources.resource_stream(__name__, file)
    return json.load(stream)


def _load_sia_codes() -> dict[str, SIACode]:
    """Alias for loading sia codes file."""
    data = _load_data(FILE_SIA_CODES)
    return {key: SIACode(**value) for (key, value) in data.items()}


def _load_xdata() -> dict[str, SIAXData]:
    """Alias for loading xdata file."""
    data = _load_data(FILE_XDATA)
    return {key: SIAXData(**value) for (key, value) in data.items()}


def _load_adm_mapping() -> dict[str, dict[str, str]]:
    """Alias for loading adm mapping file."""
    return _load_data(FILE_ADM_MAPPING)
