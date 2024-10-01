#!/usr/bin/env python3

import logging
import os
import sys
import time

import paho.mqtt.client as mqtt  # pip install paho-mqtt

"""
This script is launched by Hyprland on login
via launch_mqtt_services.sh script.
The launch config is here:
  /home/rash/.config/hypr/launch.conf
"""

# Add the custom script path to PYTHONPATH
sys.path.append("/home/rash/.config/scripts")
from _utils import logging_utils

# Configure logging
logging_utils.configure_logging()
logging.getLogger().setLevel(logging.INFO)

# MQTT connection parameters
clientname = "linux_mini_mqtt_reports"
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
file_to_topic = {
    "/tmp/mqtt/linux_mini_status": "scripts/linux_mini/status",
    "/tmp/mqtt/linux_webcam_status": "scripts/linux_webcam/status",
}

# Store previous contents
previous_contents = {}


def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        logging.info("Connected OK")
        client.publish(
            "devices/" + clientname + "/status", payload="online", qos=1, retain=True
        )
    else:
        logging.error(f'Connection failed. Returned code "{rc}"')


def on_disconnect(client, userdata, rc, properties=None):
    client.publish(
        "devices/" + clientname + "/status", payload="offline", qos=1, retain=True
    )
    logging.info(f"Disconnected for reason {rc}")


def publish_file_contents():
    for file_path, topic in file_to_topic.items():
        try:
            with open(file_path, "r") as file:
                content = file.read().strip()
                if content != previous_contents.get(file_path):
                    client.publish(topic, payload=content, qos=1, retain=True)
                    logging.info(
                        f"Published new content of {file_path} to topic {topic}"
                    )
                    previous_contents[file_path] = content
        except FileNotFoundError:
            logging.error(f"File not found: {file_path}")
        except IOError as e:
            logging.error(f"Error reading file {file_path}: {e}")


if __name__ == "__main__":

    # Connect to MQTT Broker
    client.connect(broker, connectport, keepalive)

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect

    # Start the MQTT client loop in a non-blocking way
    client.loop_start()

    try:
        while True:
            publish_file_contents()
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Script interrupted by user")
    finally:
        client.loop_stop()
        client.disconnect()
