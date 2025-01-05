#!/usr/bin/env python3

import argparse
import logging
import os
import sys
import time

import paho.mqtt.client as mqtt  # pip install paho-mqtt

# Add the custom script path to PYTHONPATH
sys.path.append("/home/rash/.config/scripts")
from _utils import logging_utils  # noqa: E402

"""
This script is launched by a systemd service.
The service file is here:
  /home/rash/.config/systemd/user/mqtt_listener.service

Status can be checked with:
  systemctl --user status mqtt_listener.service
"""

# Mapping of files to topics
topic_to_file = {
    "homeassistant/input_boolean.rob_in_office/status": "/tmp/mqtt/in_office_status",
}

# MQTT connection parameters
clientname = "linux_mini_mqtt_listener"
broker = "10.20.10.100"
connectport = 1883
keepalive = 60


def arg_parser():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="MQTT Listener for Linux")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()
    return args


def configure_logging(args):
    # Configure logging
    logging_utils.configure_logging()
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.WARNING)


def set_mqtt_client():
    client = mqtt.Client(
        client_id=clientname, callback_api_version=mqtt.CallbackAPIVersion.VERSION2
    )
    client.username_pw_set(
        username=os.environ["mqtt_user"], password=os.environ["mqtt_password"]
    )
    client.will_set(
        "devices/" + clientname + "/status", payload="offline", qos=1, retain=True
    )
    return client


def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        logging.debug("Connected OK")
        client.publish(
            "devices/" + clientname + "/status", payload="online", qos=1, retain=True
        )
        subscribe_to_topics(client)
    else:
        logging.error(f'Connection failed. Returned code "{rc}"')


def on_disconnect(client, userdata, rc, *args, properties=None):
    logging.debug(
        f"on_disconnect called with client={client}, userdata={userdata}, rc={rc}, args={args}, properties={properties}"
    )

    # Check if rc is an instance of DisconnectFlags and provide a more user-friendly message
    if isinstance(rc, mqtt.DisconnectFlags):
        if rc.is_disconnect_packet_from_server:
            logging.debug("Disconnected: Server might be down.")
        else:
            logging.debug("Disconnected: Client initiated or other reason.")
    else:
        logging.debug(f"Disconnected for reason {rc}")

    # Iterate over args and check types to ensure correct handling
    for arg in args:
        if isinstance(arg, mqtt.ReasonCode):
            logging.debug(f"Reason code for disconnection: {arg}")
        elif isinstance(arg, mqtt.Properties):  # Corrected to 'mqtt.Properties'
            logging.debug(f"Disconnection properties: {arg}")
        else:
            logging.debug(f"Unknown argument in on_disconnect: {arg}")

    client.publish(
        "devices/" + clientname + "/status", payload="offline", qos=1, retain=True
    )

    if rc != 0:
        logging.debug(
            "Unexpected disconnection. The client will attempt to reconnect automatically."
        )


def subscribe_to_topics(client):
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


def main():
    args = arg_parser()

    configure_logging(args)

    client = set_mqtt_client()

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message

    # Configure reconnect delay and enable logging
    client.reconnect_delay_set(min_delay=30, max_delay=3600)
    client.enable_logger()

    try:
        # Initial connection
        client.connect(broker, connectport, keepalive)

        # Start the MQTT client loop in a non-blocking way
        client.loop_start()

        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.debug("Script interrupted by user")
    except Exception as e:
        logging.error(f"An error occurred: {e}", exc_info=True)
        sys.exit(1)
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
