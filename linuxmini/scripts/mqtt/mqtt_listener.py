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
    "homeassistant/binary_sensor.rob_in_office/status": "/tmp/mqtt/in_office_status",
}

# MQTT connection parameters
clientname = "linux_mini_mqtt_listener"
broker = "10.20.10.100"
connectport = 1883
keepalive = 60

# Broker status monitoring
BROKER_STATUS_TOPIC = "homeassistant/status"  # Home Assistant's broker status topic
broker_online = False


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
    logging.debug("Creating MQTT client...")
    client = mqtt.Client(client_id=clientname)
    client.username_pw_set(
        username=os.environ["mqtt_user"], password=os.environ["mqtt_password"]
    )
    client.will_set(
        "devices/" + clientname + "/status", payload="offline", qos=1, retain=True
    )
    logging.info("MQTT client created successfully")
    return client


def on_connect(client, userdata, flags, rc):
    global broker_online
    logging.debug(f"on_connect called with rc={rc}, flags={flags}")
    if rc == 0:
        logging.info("Connected OK to MQTT broker")
        broker_online = True

        logging.debug("Publishing online status...")
        status_result = client.publish(
            "devices/" + clientname + "/status", payload="online", qos=1, retain=True
        )
        if status_result.rc != mqtt.MQTT_ERR_SUCCESS:
            logging.warning(
                f"Failed to publish online status: {mqtt.error_string(status_result.rc)}"
            )
        else:
            logging.debug(f"Online status publish result: {status_result.rc}")

        logging.debug("Subscribing to broker status...")
        sub_result = client.subscribe(BROKER_STATUS_TOPIC, qos=1)
        if sub_result[0] != mqtt.MQTT_ERR_SUCCESS:
            logging.warning(
                f"Failed to subscribe to {BROKER_STATUS_TOPIC}: {mqtt.error_string(sub_result[0])}"
            )
        else:
            logging.debug(f"Subscription result: {sub_result}")

        logging.debug("Subscribing to topics...")
        subscribe_to_topics(client)
    else:
        logging.error(f'Connection failed. Returned code "{rc}"')


def on_connect_fail(client, userdata):
    """Called when TCP connection to broker fails."""
    logging.warning("TCP connection to MQTT broker failed, will retry...")


def on_disconnect(client, userdata, rc):
    global broker_online
    broker_online = False
    if rc == 0:
        logging.info("Disconnected cleanly")
    else:
        logging.warning(f"Unexpected disconnect (rc={rc}), paho-mqtt will auto-reconnect")


def subscribe_to_topics(client):
    for topic in topic_to_file.keys():
        logging.debug(f"Subscribing to topic: {topic}")
        sub_result = client.subscribe(topic, qos=1)
        if sub_result[0] != mqtt.MQTT_ERR_SUCCESS:
            logging.warning(
                f"Failed to subscribe to {topic}: {mqtt.error_string(sub_result[0])}"
            )
        else:
            logging.debug(f"Subscription result for {topic}: {sub_result}")


def on_message(client, userdata, message):
    global broker_online
    topic = message.topic
    payload = message.payload.decode()
    logging.debug(f"Received message on topic {topic}: {payload}")

    if topic == BROKER_STATUS_TOPIC:
        if payload == "offline" and broker_online:
            logging.warning("Broker status changed to offline")
            broker_online = False
        elif payload == "online" and not broker_online:
            logging.info("Broker status changed to online")
            broker_online = True
    else:
        file_path = topic_to_file.get(topic)
        if file_path:
            logging.debug(f"Processing message for file: {file_path}")
            try:
                dir_path = os.path.dirname(file_path)
                if not os.path.exists(dir_path):
                    logging.debug(f"Creating directory: {dir_path}")
                    os.makedirs(dir_path)
                write_status_file(file_path, payload)
                logging.debug(f"Successfully wrote to file: {file_path}")
            except IOError as e:
                logging.warning(f"Failed to write to file {file_path}: {e}")
            except Exception as e:
                logging.error(f"Unexpected error writing to file: {e}", exc_info=True)
        else:
            logging.debug(f"No file mapping found for topic: {topic}")


def write_status_file(file_path, payload):
    with open(file_path, "w") as file:
        file.write(payload)


def main():
    args = arg_parser()
    configure_logging(args)
    logging.info("Starting MQTT Listener Service")

    client = set_mqtt_client()
    client.on_connect = on_connect
    client.on_connect_fail = on_connect_fail
    client.on_disconnect = on_disconnect
    client.on_message = on_message

    logging.debug("Configuring reconnect delay...")
    client.reconnect_delay_set(min_delay=1, max_delay=300)
    logging.debug("Enabling MQTT logger...")
    client.enable_logger()

    try:
        logging.debug(f"Connecting to MQTT broker at {broker}:{connectport}...")
        client.connect(broker, connectport, keepalive)
        logging.debug("Initial connection established")

        logging.debug("Starting MQTT loop...")
        client.loop_forever()
    except KeyboardInterrupt:
        logging.info("MQTT Listener Service interrupted by user")
    except Exception as e:
        logging.error(f"Unhandled error occurred: {e}", exc_info=True)
    finally:
        logging.debug("Shutting down MQTT client...")
        client.disconnect()
        logging.debug("MQTT client shutdown complete")


if __name__ == "__main__":
    main()
