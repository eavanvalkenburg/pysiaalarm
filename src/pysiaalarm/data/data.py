
"""Data related utils for pysiaalarm."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, TypedDict 



class SIACodeData(TypedDict):
    """TypedDict pour la structure des données brutes pour SIACode."""
    code: str
    type: str
    description: str
    concerns: str

class SIAXDataDict(TypedDict):
    """TypedDict pour la structure des données brutes pour SIAXData."""
    identifier: str
    name: str
    description: str
    length: int
    characters: str
    value: Optional[str] 

from .adm_mapping import ADM_MAPPING
from .sia_codes import SIA_CODES
from .xdata import XDATA


@dataclass
class SIACode:
    """Classe pour les codes SIA.

    Cette dataclass représente un code SIA structuré avec ses propriétés.
    """
    code: str
    type: str
    description: str
    concerns: str


@dataclass
class SIAXData:
    """Classe pour les données Xdata.

    Cette dataclass représente un élément de donnée Xdata étendu.
    """
    identifier: str
    name: str
    description: str
    length: int
    characters: str
    value: Optional[str] = None 


def _load_sia_codes() -> Dict[str, SIACode]:
    """Charge les codes SIA à partir du fichier de données.

    Retourne un dictionnaire où les clés sont les codes SIA et les valeurs
    sont des instances de SIACode.
    """

    return {key: SIACode(**value) for (key, value) in SIA_CODES.items()}


def _load_xdata() -> Dict[str, SIAXData]:
    """Charge les données Xdata à partir du fichier de données.

    Retourne un dictionnaire où les clés sont les identifiants Xdata et les valeurs
    sont des instances de SIAXData.
    """

    return {key: SIAXData(**value) for (key, value) in XDATA.items()}


def _load_adm_mapping() -> Dict[str, Dict[str, str]]:
    """Charge le mappage ADM (Account/Device/Modifier) à partir du fichier de données.

    Retourne un dictionnaire pour le mappage des codes ADM.
    """
    return ADM_MAPPING