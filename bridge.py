"""
bridge.py — Boucle principale du bridge TIC → MQTT.

Responsabilités :
  - Ouverture et supervision du port série (reconnexion automatique)
  - Détection des trames TIC (STX 0x02 / ETX 0x03)
  - Rate-limiting (PUBLISH_INTERVAL secondes entre deux publications)
  - Orchestration : parser → payload → publisher
"""

import logging
import signal
import time
from typing import Optional

import serial

import config
from mqtt_client import MQTTClient
from tic_parser  import parse_frame
from payload     import structure_payload
from publisher   import publish_all

log = logging.getLogger(__name__)


# ── Ouverture du port série ────────────────────────────────────────────────────

def _open_serial() -> serial.Serial:
    parity_map = {
        "E": serial.PARITY_EVEN,
        "N": serial.PARITY_NONE,
        "O": serial.PARITY_ODD,
    }
    return serial.Serial(
        port     = config.SERIAL_PORT,
        baudrate = config.SERIAL_BAUD,
        bytesize = config.SERIAL_BITS,
        parity   = parity_map.get(config.SERIAL_PARITY.upper(), serial.PARITY_EVEN),
        stopbits = config.SERIAL_STOPS,
        timeout  = 10,
    )


# ── Boucle principale ──────────────────────────────────────────────────────────

def run(mqtt: MQTTClient) -> None:
    """
    Lit le port série en continu, détecte les trames TIC et les publie sur MQTT.
    S'arrête proprement sur SIGTERM ou SIGINT.
    """
    log.info(
        "Bridge démarré — port=%s  broker=%s:%s  prefix=%s  interval=%ss",
        config.SERIAL_PORT, config.MQTT_HOST, config.MQTT_PORT,
        config.MQTT_PREFIX, config.PUBLISH_INTERVAL,
    )

    running = True

    def _stop(sig, _frame):
        nonlocal running
        log.info("Signal %s reçu → arrêt propre", sig)
        running = False

    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT,  _stop)

    ser: Optional[serial.Serial] = None
    frame_buf = bytearray()
    in_frame  = False
    last_pub  = 0.0

    while running:

        # ── Connexion / reconnexion série ──────────────────────────────────────
        if ser is None or not ser.is_open:
            try:
                ser = _open_serial()
                log.info("Port série ouvert : %s", config.SERIAL_PORT)
            except serial.SerialException as exc:
                log.error("Impossible d'ouvrir %s : %s  → retry dans 10 s",
                          config.SERIAL_PORT, exc)
                time.sleep(10)
                continue

        # ── Lecture octet par octet ────────────────────────────────────────────
        try:
            byte = ser.read(1)
        except serial.SerialException as exc:
            log.error("Erreur lecture série : %s", exc)
            _close_serial(ser)
            ser = None
            continue

        if not byte:
            continue

        b = byte[0]

        if b == 0x02:               # STX — début de trame
            frame_buf = bytearray()
            in_frame  = True

        elif b == 0x03:             # ETX — fin de trame
            if in_frame and frame_buf:
                if _process_frame(mqtt, bytes(frame_buf), last_pub):
                    last_pub = time.time()
            in_frame  = False
            frame_buf = bytearray()

        elif in_frame:
            frame_buf.append(b)

    # ── Nettoyage ──────────────────────────────────────────────────────────────
    _close_serial(ser)
    log.info("Bridge arrêté")


# ── Traitement d'une trame complète ───────────────────────────────────────────

def _process_frame(mqtt: MQTTClient, raw: bytes, last_pub: float) -> bool:
    """Parse, structure et publie une trame si l'intervalle est écoulé.
    Retourne True si une publication a eu lieu."""
    now = time.time()
    if now - last_pub < config.PUBLISH_INTERVAL:
        log.debug("Trame ignorée (rate-limit, %.1f s restantes)",
                  config.PUBLISH_INTERVAL - (now - last_pub))
        return False

    raw_data = parse_frame(raw)
    if not raw_data:
        log.debug("Trame vide ou entièrement invalide — ignorée")
        return False

    data = structure_payload(raw_data)
    publish_all(mqtt, data)
    log.info("Trame publiée — %d étiquettes TIC", len(raw_data))
    return True


def _close_serial(ser: Optional[serial.Serial]) -> None:
    if ser:
        try:
            ser.close()
        except Exception:
            pass
