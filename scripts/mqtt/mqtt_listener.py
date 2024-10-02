#!/usr/bin/env python3

import argparse
import logging
import os
import sys
import time

import paho.mqtt.client as mqtt  # pip install paho-mqtt

# Add the custom script path to PYTHONPATH
sys.path.append("/home/rash/.config/scripts")
from _utils import logging_utils

"""
This script is launched by Hyprland on login
via launch_mqtt_services.sh script.
The launch config is here:
  /home/rash/.config/hypr/launch.conf
"""

# Parse command-line arguments
parser = argparse.ArgumentParser(description="MQTT Listener for Linux")
parser.add_argument("--debug", action="store_true", help="Enable debug logging")
args = parser.parse_args()

# Configure logging
logging_utils.configure_logging()
if args.debug:
    logging.getLogger().setLevel(logging.DEBUG)
else:
    logging.getLogger().setLevel(logging.ERROR)

# MQTT connection parameters
clientname = "linux_mini_mqtt_listener"
broker = "10.20.10.100"
connectport = 1883
keepalive = 60
client = mqtt.Client(
    client_id=clientname, callback_api_version=mqtt.CallbackAPIVersion.VERSION2
)
client.username_pw_set(
    username=os.environ["mqtt_user"], password=os.environ["mqtt_password"]
)
client.will_set(
    "devices/" + clientname + "/status", payload="offline", qos=1, retain=True
)

# Mapping of files to topics
topic_to_file = {
    "homeassistant/input_boolean.rob_in_office/status": "/tmp/mqtt/in_office_status",
}


def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        logging.debug("Connected OK")
        client.publish(
            "devices/" + clientname + "/status", payload="online", qos=1, retain=True
        )
        subscribe_to_topics()
    else:
        logging.error(f'Connection failed. Returned code "{rc}"')


def on_disconnect(client, userdata, rc, properties=None):
    client.publish(
        "devices/" + clientname + "/status", payload="offline", qos=1, retain=True
    )
    logging.debug(f"Disconnected for reason {rc}")


def subscribe_to_topics():
    for topic in topic_to_file.keys():
        client.subscribe(topic, qos=1)


def on_message(client, userdata, message):
    topic = message.topic
    payload = message.payload.decode()
    file_path = topic_to_file.get(topic)
    if file_path:
        # Check dir and create if not exists
        dir_path = os.path.dirname(file_path)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        write_status_file(file_path, payload)


def write_status_file(file_path, payload):
    with open(file_path, "w") as file:
        file.write(payload)


if __name__ == "__main__":

    # Connect to MQTT Broker
    client.connect(broker, connectport, keepalive)

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message

    # Start the MQTT client loop in a non-blocking way
    client.loop_start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.debug("Script interrupted by user")
    finally:
        client.loop_stop()
        client.disconnect()
