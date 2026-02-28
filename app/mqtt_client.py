"""
mqtt_client.py — Connexion au broker MQTT et publication avec RBE.
Compatible paho-mqtt 1.6.1.

RBE (Report By Exception) : un message n'est publié que si sa valeur
a changé depuis la dernière publication — comportement identique aux
nœuds 'rbe' du flow Node-RED d'origine.
"""

import logging
import time
import paho.mqtt.client as mqtt

from config import (
    MQTT_HOST, MQTT_PORT, MQTT_USER, MQTT_PASS,
    MQTT_CLIENT, MQTT_PREFIX,
)

log = logging.getLogger(__name__)

_RETRY_DELAY = 5    # secondes entre deux tentatives de connexion initiale


class MQTTClient:
    """
    Wrapper autour de paho-mqtt 1.6.1 avec :
      - retry de connexion initiale si le broker est injoignable au démarrage
      - reconnexion automatique via loop_start (paho gère le reconnect)
      - publication RBE (publish uniquement si valeur ≠ dernière valeur)
    """

    def __init__(self):
        # paho 1.6.1 : pas de reconnect_on_failure dans le constructeur
        self._client = mqtt.Client(
            client_id = MQTT_CLIENT,
            protocol  = mqtt.MQTTv5,
        )
        self._last: dict[str, str] = {}
        self._connected = False

        if MQTT_USER:
            self._client.username_pw_set(MQTT_USER, MQTT_PASS)

        # paho 1.6.1 signatures :
        #   on_connect(client, userdata, flags, rc)       ← rc est un int
        #   on_disconnect(client, userdata, rc)           ← 3 args seulement
        self._client.on_connect    = self._on_connect
        self._client.on_disconnect = self._on_disconnect

    # ── Connexion ──────────────────────────────────────────────────────────────

    def connect(self) -> None:
        """
        Tente de se connecter au broker MQTT.
        Réessaie indéfiniment avec un délai si le broker est injoignable.
        """
        attempt = 0
        while True:
            attempt += 1
            try:
                log.info("Connexion MQTT → %s:%s (tentative %d)…",
                         MQTT_HOST, MQTT_PORT, attempt)
                self._client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
                self._client.loop_start()
                # Attendre la confirmation on_connect (max 10 s)
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

        result = self._client.publish(full_topic, payload=str_value, retain=retain)

        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            log.warning("Échec publication %s (rc=%s)", full_topic, result.rc)
            return False

        self._last[full_topic] = str_value
        log.debug("MQTT ↑ %s = %s", full_topic, str_value)
        return True

    # ── Callbacks paho 1.6.1 ─────────────────────────────────────────────────

    def _on_connect(self, client, userdata, flags, rc):
        # rc=0 : succès, autres valeurs : erreur
        if rc == 0:
            self._connected = True
            log.info("MQTT connecté à %s:%s", MQTT_HOST, MQTT_PORT)
        else:
            log.error("MQTT connexion refusée (rc=%s — %s)",
                      rc, mqtt.connack_string(rc))

    def _on_disconnect(self, client, userdata, rc):
        # paho 1.6.1 : seulement 3 arguments
        self._connected = False
        if rc == 0:
            log.info("MQTT déconnecté proprement")
        else:
            log.warning("MQTT déconnecté de façon inattendue (rc=%s) — reconnexion auto…", rc)