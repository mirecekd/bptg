"""bptg — Bridge Blood Pressure Telemetry from MQTT to Garmin Connect.

Listens to an MQTT topic for blood-pressure measurements and uploads them to
Garmin Connect. Uses token-based authentication (DI OAuth) with persistent
token storage so we do not re-authenticate on every message.
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import paho.mqtt.client as mqtt
from garminconnect import (
    Garmin,
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)

# --- Configuration --------------------------------------------------------- #

broker = os.environ["MQTT_BROKER"]
port = int(os.environ["MQTT_PORT"])
mqtt_user = os.environ["MQTT_USER"]
mqtt_pass = os.environ["MQTT_PASS"]
timelive = int(os.environ["MQTT_TTL"])
topic = os.environ["MQTT_TOPIC"]
garmin_user = os.environ["GARMIN_USER"]
garmin_pass = os.environ["GARMIN_PASS"]
tokenstore = os.environ.get("GARMIN_TOKENSTORE", "/data/garminconnect")
tokenstore_path = str(Path(tokenstore).expanduser())

verbose = os.environ.get("VERBOSE", "").lower() in ("1", "true", "yes")

logging.basicConfig(
    level=logging.DEBUG if verbose else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger("bptg")

previous_data = None
garmin: Garmin | None = None


# --- Garmin authentication ------------------------------------------------- #

def init_garmin() -> Garmin:
    """Initialise Garmin API client.

    1. Try to reuse persisted DI OAuth tokens from ``tokenstore_path``.
    2. Fallback to credential login (without MFA) and save tokens for
       future runs.
    """
    Path(tokenstore_path).mkdir(parents=True, exist_ok=True)

    # 1) Try existing tokens
    try:
        g = Garmin()
        g.login(tokenstore_path)
        log.info("Garmin: logged in using saved tokens (%s)", tokenstore_path)
        return g
    except (
        FileNotFoundError,
        GarminConnectAuthenticationError,
        GarminConnectConnectionError,
    ) as exc:
        log.info("Garmin: no valid token found (%s) — falling back to credentials", exc)

    # 2) Credential login — save tokens
    g = Garmin(email=garmin_user, password=garmin_pass)
    g.login(tokenstore_path)
    log.info("Garmin: credential login successful, tokens saved to %s", tokenstore_path)
    return g


def ensure_garmin() -> Garmin:
    """Return a usable Garmin client, re-initialising on demand."""
    global garmin
    if garmin is None:
        garmin = init_garmin()
    return garmin


# --- MQTT callbacks -------------------------------------------------------- #

def on_connect(client, userdata, flags, rc):
    log.info("MQTT connected (rc=%s), subscribing to %s", rc, topic)
    client.subscribe(topic)


def on_message(client, userdata, msg):
    global previous_data, garmin

    payload_text = msg.payload.decode()
    log.debug("MQTT payload: %s", payload_text)

    try:
        data = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        log.error("MQTT payload is not valid JSON: %s", exc)
        return

    if previous_data is not None and previous_data == data:
        log.info("Data unchanged — skipping upload")
        return

    if "unavailable" in (data.get("Systolic"), data.get("Diastolic"), data.get("Pulse")):
        log.info("Skipping upload: some values are unavailable")
        return

    try:
        # garminconnect requires int values
        systolic = int(round(float(data["Systolic"])))
        diastolic = int(round(float(data["Diastolic"])))
        pulse = int(round(float(data["Pulse"])))
    except (KeyError, TypeError, ValueError) as exc:
        log.error("Cannot parse measurement values: %s", exc)
        return

    log.info(
        "Uploading BP: systolic=%s diastolic=%s pulse=%s (ts=%s)",
        systolic, diastolic, pulse, data.get("TimeStamp"),
    )

    try:
        upload_blood_pressure(systolic, diastolic, pulse)
        previous_data = data
        log.info("Blood pressure data uploaded to Garmin Connect")
    except GarminConnectTooManyRequestsError as exc:
        log.error("Garmin rate-limit hit: %s", exc)
    except (GarminConnectAuthenticationError, GarminConnectConnectionError) as exc:
        log.error("Garmin upload failed: %s", exc)


def upload_blood_pressure(systolic: float, diastolic: float, pulse: float) -> None:
    """Upload BP measurement; on auth failure re-login once and retry."""
    global garmin
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _do_upload() -> None:
        ensure_garmin().set_blood_pressure(
            timestamp=timestamp,
            systolic=systolic,
            diastolic=diastolic,
            pulse=pulse,
        )

    try:
        _do_upload()
    except GarminConnectAuthenticationError as exc:
        log.warning("Auth error during upload (%s) — re-initialising Garmin client", exc)
        garmin = None
        _do_upload()


# --- Main ------------------------------------------------------------------ #

def main() -> None:
    # Pre-authenticate before we start the MQTT loop so the first message
    # doesn't fight with login latency.
    ensure_garmin()

    client = mqtt.Client(
        client_id=mqtt_user,
        callback_api_version=mqtt.CallbackAPIVersion.VERSION1,
    )
    client.username_pw_set(mqtt_user, mqtt_pass)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(broker, port, timelive)
    client.loop_forever()


if __name__ == "__main__":
    main()
