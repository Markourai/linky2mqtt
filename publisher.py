"""
publisher.py — Calcul et publication des topics MQTT depuis le payload structuré.

Reproduit l'ensemble des nœuds de transformation (INDEX TOTAL, INDEX HC/HP,
INDEX par couleur, IINST, PAPP, PMAX, PTEC, TEMPO) et leurs nœuds 'rbe' associés.
"""

import logging
from mqtt_client import MQTTClient
from payload import PTEC_MAP

log = logging.getLogger(__name__)


def publish_all(client: MQTTClient, data: dict) -> None:
    """
    Calcule toutes les valeurs dérivées depuis le payload structuré
    et les publie via le client MQTT (avec RBE intégré).
    """

    def get(key: str, default=0):
        return data.get(key, default)

    _publish_indices(client, data, get)
    _publish_current(client, data)
    _publish_power(client, data)
    _publish_tariff(client, data)
    _publish_tempo(client, data)


# ── Indices de consommation ────────────────────────────────────────────────────

def _publish_indices(client: MQTTClient, data: dict, get) -> None:
    """Publie les index de consommation Tempo (par couleur et agrégés)."""

    hcjb = get("BBRHCJB"); hpjb = get("BBRHPJB")
    hcjw = get("BBRHCJW"); hpjw = get("BBRHPJW")
    hcjr = get("BBRHCJR"); hpjr = get("BBRHPJR")

    index_wh = hcjb + hpjb + hcjw + hpjw + hcjr + hpjr

    # ── Totaux ─────────────────────────────────────────────────────────────────
    client.publish("index_wh",      index_wh)
    client.publish("index_kwh",     _kwh(index_wh))

    # ── HP / HC global ─────────────────────────────────────────────────────────
    client.publish("index_hp_kwh",  _kwh(hpjb + hpjw + hpjr))
    client.publish("index_hc_kwh",  _kwh(hcjb + hcjw + hcjr))

    # ── Par couleur Tempo ──────────────────────────────────────────────────────
    client.publish("index_hpb_kwh", _kwh(hpjb))   # Heures Pleines Bleu
    client.publish("index_hpw_kwh", _kwh(hpjw))   # Heures Pleines Blanc
    client.publish("index_hpr_kwh", _kwh(hpjr))   # Heures Pleines Rouge
    client.publish("index_hcb_kwh", _kwh(hcjb))   # Heures Creuses Bleu
    client.publish("index_hcw_kwh", _kwh(hcjw))   # Heures Creuses Blanc
    client.publish("index_hcr_kwh", _kwh(hcjr))   # Heures Creuses Rouge


# ── Courant instantané ─────────────────────────────────────────────────────────

def _publish_current(client: MQTTClient, data: dict) -> None:
    """Publie IINST1 / IINST2 / IINST3 (mono ou triphasé)."""
    for phase in (1, 2, 3):
        key = f"IINST{phase}"
        if key in data:
            client.publish(f"iinst{phase}", data[key])


# ── Puissance ──────────────────────────────────────────────────────────────────

def _publish_power(client: MQTTClient, data: dict) -> None:
    """Publie PAPP (puissance apparente) et PMAX (puissance maximale)."""
    if "PAPP" in data:
        client.publish("papp", data["PAPP"])
    if "PMAX" in data:
        client.publish("pmax", data["PMAX"])


# ── Période tarifaire ──────────────────────────────────────────────────────────

def _publish_tariff(client: MQTTClient, data: dict) -> None:
    """Publie le libellé PTEC (ex : 'Heures Creuses')."""
    if "PTEC" not in data:
        return
    ptec_raw = data["PTEC"]
    label, _ = PTEC_MAP.get(ptec_raw, (ptec_raw, None))
    client.publish("ptec", label)


# ── Couleurs Tempo ─────────────────────────────────────────────────────────────

def _publish_tempo(client: MQTTClient, data: dict) -> None:
    """Publie la couleur Tempo du jour courant et du lendemain."""

    # Couleur du jour déduite de PTEC
    if "PTEC" in data:
        _, color = PTEC_MAP.get(data["PTEC"], (None, None))
        if color:
            client.publish("tempo_day", color)

    # Couleur du lendemain (déjà normalisée par payload.py)
    if "DEMAIN" in data and data["DEMAIN"]:
        client.publish("next_tempo_day", data["DEMAIN"])


# ── Utilitaire ─────────────────────────────────────────────────────────────────

def _kwh(wh: int | float) -> float:
    """Convertit des Wh en kWh, arrondi à 3 décimales."""
    return round(wh / 1000, 3)
