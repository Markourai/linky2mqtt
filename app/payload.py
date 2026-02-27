"""
payload.py — Transformation du payload TIC brut en valeurs typées.

Reproduit la logique du nœud Node-RED "Structure payload" :
  - Conversion des chaînes numériques en int/float
  - Décodage des champs alphanumériques (OPTARIF, PTEC, HHPHC)
  - Renommage IINST → IINST1, IMAX → IMAX1
"""

import logging

log = logging.getLogger(__name__)

# ── Tables de correspondance ───────────────────────────────────────────────────

OPTARIF_MAP = {
    "BAS": 1,  # Option Base
    "HC.": 2,  # Option Heures Creuses
    "EJP": 3,  # Option EJP
    "BBR": 4,  # Option Tempo (BBRx)
}

# PTEC : (libellé lisible, couleur Tempo ou None)
PTEC_MAP: dict[str, tuple[str, str | None]] = {
    "TH..": ("Toutes Heures",        None),
    "HC..": ("Heures Creuses",       None),
    "HP..": ("Heures Pleines",       None),
    "HN..": ("Heures Normales",      None),
    "PM..": ("Heures Pointe Mobile", None),
    "HCJB": ("Heures Creuses",       "BLUE"),
    "HCJW": ("Heures Creuses",       "WHITE"),
    "HCJR": ("Heures Creuses",       "RED"),
    "HPJB": ("Heures Pleines",       "BLUE"),
    "HPJW": ("Heures Pleines",       "WHITE"),
    "HPJR": ("Heures Pleines",       "RED"),
}

# DEMAIN : préfixe 4 chars → couleur Tempo normalisée
DEMAIN_MAP = {
    "BLEU": "BLUE",
    "BLAN": "WHITE",
    "ROUG": "RED",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _is_numeric(v: str) -> bool:
    try:
        float(v)
        return True
    except ValueError:
        return False


def _to_number(v: str) -> int | float:
    """Convertit en int si possible, sinon float."""
    f = float(v)
    return int(f) if f == int(f) else f


# ── Structuration principale ───────────────────────────────────────────────────

def structure_payload(raw: dict[str, str]) -> dict:
    """
    Prend le dict { LABEL: str } issu du parseur TIC et retourne un dict
    avec des valeurs correctement typées (int, float ou str selon le champ).
    """
    data: dict = {}

    for label, value in raw.items():

        if label == "OPTARIF":
            # 4 chars alphanumériques → int (on ignore le 4e char)
            key = value[:3]
            data[label] = OPTARIF_MAP.get(key, 0)

        elif label == "HHPHC":
            # Caractère A–Y → code ASCII
            data[label] = ord(value[0]) if value else 0

        elif label == "PTEC":
            # Conservé en chaîne brute ; la conversion lisible est faite dans publisher.py
            data[label] = value

        elif label == "DEMAIN":
            # Normalisation de la couleur Tempo du lendemain
            key = value[:4].upper()
            data[label] = DEMAIN_MAP.get(key, value) if value.strip() != "----" else ""

        elif label == "IINST":
            # Monophasé : IINST → IINST1 (cohérence avec le triphasé)
            data["IINST1"] = _to_number(value) if _is_numeric(value) else value

        elif label == "IMAX":
            # Monophasé : IMAX → IMAX1
            data["IMAX1"] = _to_number(value) if _is_numeric(value) else value

        elif label == "ADCO":
            # Identifiant compteur : ne pas convertir en numérique
            data[label] = value

        elif _is_numeric(value):
            data[label] = _to_number(value)

        else:
            data[label] = value

    log.debug("Payload structuré : %d champs", len(data))
    return data
