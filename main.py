"""
main.py — Linky TIC to MQTT for Home Assistant.
Inspired by soria2mqtt (https://github.com/Markourai/soria2mqtt)

Reads data from a linky TIC on USB serial,
decodes the linky message
and publishes measurements to MQTT with Home Assistant auto-discovery.
"""

import logging
from mqtt_client import MQTTClient
from bridge import run

VERSION = "1.0.5"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)

logger = logging.getLogger('linky2mqtt')

def main():
    logger.info("=" * 50)
    logger.info("  linky2mqtt — Linky TIC to MQTT")
    logger.info("  version: %s  ", VERSION)
    logger.info("=" * 50)
    mqtt = MQTTClient()
    mqtt.connect()
    try:
        run(mqtt)
    finally:
        mqtt.disconnect()


if __name__ == "__main__":
    main()
