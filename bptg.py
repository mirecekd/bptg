import paho.mqtt.client as mqtt
import json
import os
import logging
import sys

from datetime import datetime

from garminconnect import (
    Garmin,
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)

broker = os.environ['MQTT_BROKER']
port = int(os.environ['MQTT_PORT'])
username = os.environ['MQTT_USER']
password = os.environ['MQTT_PASS']
timelive = int(os.environ['MQTT_TTL'])
topic = os.environ['MQTT_TOPIC']
garmin_user = os.environ['GARMIN_USER']
garmin_pass = os.environ['GARMIN_PASS']
verbose = False
previous_data = None

logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    stream=sys.stdout)


def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe(topic)


def on_message(client, userdata, msg):
    global previous_data
    print(msg.payload.decode())

    data = json.loads(msg.payload.decode())

    if previous_data is not None and previous_data == data:
      print("Data has not changed. Skipping upload.")
      return

    values = {
        'Systolic': None,
        'Diastolic': None,
        'timestamp': None
    }

    print("MQTT payload decoded")

    values['timestamp'] = data['TimeStamp']
    values['systolic'] = float(data["Systolic"])
    values['diastolic'] = float(data["Diastolic"])    
    values['pulse'] = float(data["Pulse"])    

    print(values)

    garmin = Garmin(garmin_user, garmin_pass)
    garmin.login()
    garmin.set_blood_pressure(
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        systolic=values['systolic'],
        diastolic=values['diastolic'],
        pulse=values['pulse']
    )

    print('Blood pressure data uploaded to Garmin Connect')

    previous_data = data


client = mqtt.Client(username)
client.username_pw_set(username, password)
client.connect(broker, port, timelive)
client.on_connect = on_connect
client.on_message = on_message
client.loop_forever()
