"""Data related utils for pysiaalarm."""

from __future__ import annotations # Garder cette ligne pour les versions futures (>3.9)

from dataclasses import dataclass
from typing import Dict, Optional, Any # <-- AJOUTEZ Dict, Optional, Any

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
    value: Optional[str] = None # <-- Utilisation de Optional[str] pour la compatibilité < Python 3.10


def _load_sia_codes() -> Dict[str, SIACode]: # <-- Utilisation de Dict du module typing
    """Alias for loading sia codes file."""
    # mypy peut toujours se plaindre si SIA_CODES n'est pas typé précisément comme
    # Dict[str, Dict[str, str]] ou mieux, un TypedDict.
    # Pour le moment, si SIA_CODES est garanti de contenir les clés 'code', 'type', 'description', 'concerns'
    # en tant que str, l'initialisation avec **value fonctionnera à l'exécution.
    # Si mypy persiste, vous pourriez avoir besoin de typer explicitement SIA_CODES
    # dans son propre fichier, ou d'utiliser un cast ici (mais c'est moins idéal).
    # Exemple de cast (à n'utiliser que si mypy ne peut pas inférer le type autrement):
    # from typing import cast
    # return {key: SIACode(**cast(Dict[str, str], value)) for (key, value) in SIA_CODES.items()}
    return {key: SIACode(**value) for (key, value) in SIA_CODES.items()}


def _load_xdata() -> Dict[str, SIAXData]: # <-- Utilisation de Dict du module typing
    """Alias for loading xdata file."""
    # Comme pour _load_sia_codes, mypy peut se plaindre ici si XDATA n'est pas précisément typé.
    # L'erreur initiale de "Argument 1 to SIAXData..." est due à la confusion
    # entre les arguments positionnels et les arguments par mots-clés lors de la décomposition.
    # En corrigeant les annotations de type (Dict au lieu de dict), mypy a plus d'informations.
    # Si XDATA est un dictionnaire de dictionnaires, où chaque sous-dictionnaire correspond
    # aux champs de SIAXData, cela devrait fonctionner.
    return {key: SIAXData(**value) for (key, value) in XDATA.items()}


def _load_adm_mapping() -> Dict[str, Dict[str, str]]: # <-- Utilisation de Dict du module typing
    """Alias for loading adm mapping file."""
    return ADM_MAPPING
