"""
tic_parser.py — Décodage et validation des trames TIC historique (mode standard Linky).

Protocole : chaque trame est délimitée par STX (0x02) et ETX (0x03).
Chaque ligne contient : LABEL SP VALEUR SP CHECKSUM CR LF
"""

import logging

log = logging.getLogger(__name__)


def _validate_checksum(label: str, value: str, check: str) -> bool:
    """
    Calcule la checksum TIC historique et la compare à celle reçue.

    Algorithme : somme des codes ASCII de (label + ' ' + value), modulo 256,
    masque 0x3F, décalé de +32.
    """
    total = 32  # espace séparateur entre label et valeur
    for c in label:
        total += ord(c)
    for c in value:
        total += ord(c)
    expected = chr(((total % 256) & 0x3F) + 32)
    return expected == check


def parse_frame(raw: bytes) -> dict[str, str]:
    """
    Décode une trame TIC brute (contenu entre STX et ETX, délimiteurs inclus).

    Retourne un dict { LABEL: valeur_brute_string } pour les lignes dont
    la checksum est correcte. Les lignes invalides sont simplement ignorées
    (avec un log debug).
    """
    teleinfo: dict[str, str] = {}

    try:
        text = raw.decode("ascii", errors="ignore")
    except Exception as exc:
        log.warning("Impossible de décoder la trame : %s", exc)
        return teleinfo

    # Supprimer les délimiteurs de trame
    text = text.replace("\x02\n", "").replace("\r\x03", "")

    for line in text.split("\r\n"):
        line = line.strip()
        if not line:
            continue

        # La checksum peut être un espace, ce qui complique le split.
        # On remplace "  " (espace-espace) par "espace-sentinel" avant de splitter.
        SENTINEL = "\x00"
        parts = line.replace("  ", f" {SENTINEL}").split(" ")

        if len(parts) < 3:
            log.debug("Ligne ignorée (format inattendu) : %r", line)
            continue

        check = parts.pop()
        value = parts.pop()
        label = parts.pop() if parts else ""

        # Rétablir le vrai caractère si la checksum était un espace
        if check == SENTINEL:
            check = " "

        if _validate_checksum(label, value, check):
            teleinfo[label] = value
        else:
            log.debug("Checksum KO — label=%r value=%r check=%r", label, value, check)

    return teleinfo
