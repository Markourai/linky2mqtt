"""
mqtt_client.py — Connexion au broker MQTT et publication avec RBE.

RBE (Report By Exception) : un message n'est publié que si sa valeur
a changé depuis la dernière publication — comportement identique aux
nœuds 'rbe' du flow Node-RED d'origine.
"""

import logging
import paho.mqtt.client as mqtt

from config import (
    MQTT_HOST, MQTT_PORT, MQTT_USER, MQTT_PASS,
    MQTT_CLIENT, MQTT_PREFIX,
)

log = logging.getLogger(__name__)


class MQTTClient:
    """
    Wrapper autour de paho-mqtt avec :
      - reconnexion automatique (loop_start)
      - publication RBE (publish uniquement si valeur ≠ dernière valeur)
    """

    def __init__(self):
        self._client = mqtt.Client(client_id=MQTT_CLIENT, protocol=mqtt.MQTTv5)
        self._last: dict[str, str] = {}   # cache RBE : topic → dernière valeur publiée

        if MQTT_USER:
            self._client.username_pw_set(MQTT_USER, MQTT_PASS)

        self._client.on_connect    = self._on_connect
        self._client.on_disconnect = self._on_disconnect

    # ── Connexion ──────────────────────────────────────────────────────────────

    def connect(self) -> None:
        """Ouvre la connexion et démarre la boucle réseau en arrière-plan."""
        self._client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
        self._client.loop_start()
        log.info("MQTT → connexion à %s:%s (client_id=%s)", MQTT_HOST, MQTT_PORT, MQTT_CLIENT)

    def disconnect(self) -> None:
        """Arrêt propre."""
        self._client.loop_stop()
        self._client.disconnect()
        log.info("MQTT déconnecté")

    # ── Publication ────────────────────────────────────────────────────────────

    def publish(self, topic: str, value, retain: bool = True) -> bool:
        """
        Publie `value` sur `{MQTT_PREFIX}/{topic}`.
        Retourne True si le message a bien été envoyé, False si ignoré (RBE).
        """
        full_topic = f"{MQTT_PREFIX}/{topic}"
        str_value  = str(value)

        if self._last.get(full_topic) == str_value:
            return False   # RBE : pas de changement

        self._client.publish(full_topic, payload=str_value, retain=retain)
        self._last[full_topic] = str_value
        log.debug("MQTT ↑ %s = %s", full_topic, str_value)
        return True

    # ── Callbacks paho ─────────────────────────────────────────────────────────

    @staticmethod
    def _on_connect(client, userdata, flags, reason_code, properties=None):
        log.info("MQTT connecté (rc=%s)", reason_code)

    @staticmethod
    def _on_disconnect(client, userdata, reason_code, properties=None):
        log.warning("MQTT déconnecté (rc=%s) — reconnexion automatique…", reason_code)
