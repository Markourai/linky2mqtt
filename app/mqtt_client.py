"""
mqtt_client.py — Connexion au broker MQTT et publication avec RBE.
Compatible paho-mqtt 1.6.1 et 2.x.
"""

import logging
import time
import paho.mqtt.client as mqtt

from config import (
    MQTT_HOST, MQTT_PORT, MQTT_USER, MQTT_PASS,
    MQTT_CLIENT, MQTT_PREFIX,
)

log = logging.getLogger(__name__)

_RETRY_DELAY = 5

# Codes d'erreur CONNACK pour diagnostic
_CONNACK_ERRORS = {
    1: "Protocole MQTT refusé (version incompatible avec le broker)",
    2: "Client ID refusé (interdit ou déjà connecté)",
    3: "Broker indisponible",
    4: "Mauvais nom d'utilisateur ou mot de passe",
    5: "Non autorisé (ACL / droits insuffisants)",
}


class MQTTClient:

    def __init__(self):
        self._client = mqtt.Client(
            client_id = MQTT_CLIENT,
            protocol  = mqtt.MQTTv5,
        )
        self._last: dict[str, str] = {}
        self._connected = False

        if MQTT_USER:
            self._client.username_pw_set(MQTT_USER, MQTT_PASS)
            log.info("Auth MQTT : user=%r  pass=%r", MQTT_USER, "*" * len(MQTT_PASS))
        else:
            log.info("Auth MQTT : anonyme (pas de user/pass)")

        log.info("Client MQTT : id=%r  protocol=MQTTv5  broker=%s:%s",
                 MQTT_CLIENT, MQTT_HOST, MQTT_PORT)

        self._client.on_connect    = self._on_connect
        self._client.on_disconnect = self._on_disconnect

    # ── Connexion ──────────────────────────────────────────────────────────────

    def connect(self) -> None:
        attempt = 0
        while True:
            attempt += 1
            try:
                log.info("Connexion MQTT (tentative %d)…", attempt)
                self._client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
                self._client.loop_start()
                for _ in range(20):
                    if self._connected:
                        return
                    time.sleep(0.5)
                log.warning("Pas de réponse du broker après 10 s — on continue quand même")
                return

            except OSError as exc:
                log.error("Connexion MQTT échouée : %s — retry dans %d s", exc, _RETRY_DELAY)
                time.sleep(_RETRY_DELAY)

    def disconnect(self) -> None:
        self._client.loop_stop()
        self._client.disconnect()
        log.info("MQTT déconnecté")

    # ── Publication ────────────────────────────────────────────────────────────

    def publish(self, topic: str, value, retain: bool = True) -> bool:
        full_topic = f"{MQTT_PREFIX}/{topic}"
        str_value  = str(value)

        if self._last.get(full_topic) == str_value:
            return False

        result = self._client.publish(full_topic, payload=str_value, retain=retain)

        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            log.warning("Échec publication %s (rc=%s)", full_topic, result.rc)
            return False

        self._last[full_topic] = str_value
        log.debug("MQTT ↑ %s = %s", full_topic, str_value)
        return True

    # ── Callbacks compatibles paho 1.6.1 ET 2.x ──────────────────────────────

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        # En MQTTv5, rc est un objet ReasonCode ; on le convertit en int
        rc_int = int(rc) if hasattr(rc, 'value') else rc
        if rc_int == 0:
            self._connected = True
            log.info("MQTT connecté à %s:%s", MQTT_HOST, MQTT_PORT)
        else:
            detail = _CONNACK_ERRORS.get(rc_int, "Erreur inconnue")
            log.error("MQTT connexion refusée — rc=%s : %s", rc_int, detail)
            log.error("  → Vérifier : user=%r  broker=%s:%s  client_id=%r",
                      MQTT_USER, MQTT_HOST, MQTT_PORT, MQTT_CLIENT)

    def _on_disconnect(self, client, userdata, rc, properties=None):
        self._connected = False
        rc_int = int(rc) if hasattr(rc, 'value') else rc
        if rc_int == 0:
            log.info("MQTT déconnecté proprement")
        else:
            log.warning("MQTT déconnecté de façon inattendue (rc=%s) — reconnexion auto…", rc_int)