"""
config.py — Paramètres centralisés (chargés depuis .env / variables d'environnement)
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── Port série ─────────────────────────────────────────────────────────────────
SERIAL_PORT     = os.getenv("SERIAL_PORT",   "/dev/ttyUSB0")
SERIAL_BAUD     = int(os.getenv("SERIAL_BAUD",   "1200"))
SERIAL_BITS     = int(os.getenv("SERIAL_BITS",   "7"))
SERIAL_PARITY   = os.getenv("SERIAL_PARITY", "E")   # E=Even, N=None, O=Odd
SERIAL_STOPS    = int(os.getenv("SERIAL_STOPS",  "1"))

# ── Broker MQTT ────────────────────────────────────────────────────────────────
MQTT_HOST       = os.getenv("MQTT_HOST",   "mqtt.marescq.fr")
MQTT_PORT       = int(os.getenv("MQTT_PORT",   "1883"))
MQTT_USER       = os.getenv("MQTT_USER",   "")
MQTT_PASS       = os.getenv("MQTT_PASS",   "")
MQTT_CLIENT     = os.getenv("MQTT_CLIENT", "linky2mqtt")
MQTT_PREFIX     = os.getenv("MQTT_PREFIX", "edf")

# ── Comportement du bridge ─────────────────────────────────────────────────────
# Intervalle minimum entre deux publications (équivalent nœud delay 1/15s Node-RED)
PUBLISH_INTERVAL = float(os.getenv("PUBLISH_INTERVAL", "15"))
