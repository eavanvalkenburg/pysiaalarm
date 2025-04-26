"""Data related utils for pysiaalarm."""

from __future__ import annotations

from dataclasses import dataclass

from .adm_mapping import ADM_MAPPING
from .sia_codes import SIA_CODES
from .xdata import XDATA


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


def _load_sia_codes() -> dict[str, SIACode]:
    """Alias for loading sia codes file."""
    return {key: SIACode(**value) for (key, value) in SIA_CODES.items()}


def _load_xdata() -> dict[str, SIAXData]:
    """Alias for loading xdata file."""
    return {key: SIAXData(**value) for (key, value) in XDATA.items()}


def _load_adm_mapping() -> dict[str, dict[str, str]]:
    """Alias for loading adm mapping file."""
    return ADM_MAPPING
