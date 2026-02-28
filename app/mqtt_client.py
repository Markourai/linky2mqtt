"""
mqtt_client.py — Connexion au broker MQTT et publication avec RBE.
Cible : paho-mqtt 1.6.1 exclusivement.
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

_CONNACK_ERRORS = {
    1: "Protocole MQTT refusé (version incompatible avec le broker)",
    2: "Client ID refusé (interdit ou déjà connecté)",
    3: "Broker indisponible",
    4: "Mauvais nom d'utilisateur ou mot de passe",
    5: "Non autorisé (ACL / droits insuffisants)",
}


class MQTTClient:

    def __init__(self):
        # paho 1.6.1 : Client(client_id, clean_session, userdata, protocol)
        self._client = mqtt.Client(
            client_id = MQTT_CLIENT,
            protocol  = mqtt.MQTTv5,
        )
        self._last: dict[str, str] = {}
        self._connected = False

        if MQTT_USER:
            self._client.username_pw_set(MQTT_USER, MQTT_PASS)
            log.info("Auth MQTT : user=%r  pass_len=%d", MQTT_USER, len(MQTT_PASS))
        else:
            log.warning("Auth MQTT : MQTT_USER vide — connexion anonyme")

        log.info("Client MQTT : id=%r  broker=%s:%s", MQTT_CLIENT, MQTT_HOST, MQTT_PORT)

        # paho 1.6.1 : on_connect(client, userdata, flags, rc)    ← rc = int
        #              on_disconnect(client, userdata, rc)          ← 3 args
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
                log.error("Connexion échouée : %s — retry dans %d s", exc, _RETRY_DELAY)
                time.sleep(_RETRY_DELAY)

    def disconnect(self) -> None:
        self._client.loop_stop()
        self._client.disconnect()
        log.info("MQTT déconnecté")

    # ── Publication RBE ────────────────────────────────────────────────────────

    def publish(self, topic: str, value, retain: bool = True) -> bool:
        full_topic = f"{MQTT_PREFIX}/{topic}"
        str_value  = str(value)

        if self._last.get(full_topic) == str_value:
            return False   # RBE : pas de changement, on n'envoie pas

        result = self._client.publish(full_topic, payload=str_value, retain=retain)
        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            log.warning("Échec publication %s (rc=%s)", full_topic, result.rc)
            return False

        self._last[full_topic] = str_value
        log.debug("MQTT ↑ %s = %s", full_topic, str_value)
        return True

    # ── Callbacks paho 1.6.1 ─────────────────────────────────────────────────

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self._connected = True
            log.info("MQTT connecté à %s:%s", MQTT_HOST, MQTT_PORT)
        else:
            detail = _CONNACK_ERRORS.get(rc, f"Erreur inconnue")
            log.error("MQTT connexion refusée (rc=%d) : %s", rc, detail)

    def _on_disconnect(self, client, userdata, rc):
        self._connected = False
        if rc == 0:
            log.info("MQTT déconnecté proprement")
        else:
            log.warning("MQTT déconnecté de façon inattendue (rc=%d) — reconnexion auto…", rc)