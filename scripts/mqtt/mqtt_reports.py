#!/usr/bin/env python3

import argparse
import logging
import os
import signal
import sys
import time

import paho.mqtt.client as mqtt  # pip install paho-mqtt
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

# Add the custom script path to PYTHONPATH
sys.path.append("/home/rash/.config/scripts")
from _utils import logging_utils  # noqa: E402

"""
This script is launched by a systemd service.
The service file is here:
  /home/rash/.config/systemd/user/mqtt_reports.service

Status can be checked with:
  systemctl --user status mqtt_reports.service
"""

# Mapping of files to topics
file_to_topic = {
    "/tmp/mqtt/linux_mini_status": "scripts/linux_mini/status",
    "/tmp/mqtt/linux_webcam_status": "scripts/linux_webcam/status",
}

# Store previous contents
previous_contents = {}

# MQTT connection parameters
clientname = "linux_mini_mqtt_reports"
broker = "10.20.10.100"
connectport = 1883
keepalive = 60


def arg_parser():
    parser = argparse.ArgumentParser(description="MQTT Reports for Linux")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    return parser.parse_args()


def configure_logging(args):
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
        for file_path in file_to_topic.keys():
            publish_file_contents(client, file_path)
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


def publish_file_contents(client, file_path):
    topic = file_to_topic.get(file_path)
    if topic:
        try:
            with open(file_path, "r") as file:
                content = file.read().strip()
                if content != previous_contents.get(file_path):
                    result = client.publish(topic, payload=content, qos=1, retain=True)
                    logging.debug(
                        f"Published to {topic}: {content}, MQTT result: {result.rc}"
                    )
                    previous_contents[file_path] = content
        except FileNotFoundError:
            logging.error(f"File not found: {file_path}")
        except IOError as e:
            logging.error(f"Error reading file {file_path}: {e}")


class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, client):
        self.client = client

    def on_modified(self, event):
        if event.src_path in file_to_topic:
            logging.debug(f"Detected change in {event.src_path}")
            publish_file_contents(self.client, event.src_path)


def setup_watchdog(client):
    event_handler = FileChangeHandler(client)
    observer = Observer()

    for file_path in file_to_topic.keys():
        dir_path = os.path.dirname(file_path)
        observer.schedule(event_handler, path=dir_path, recursive=False)
        logging.debug(f"Watchdog setup and monitoring directory: {dir_path}")

    observer.start()
    logging.debug("Watchdog is now waiting for file changes...")
    return observer


def stop_services(observer, client):
    logging.debug("Shutting down services...")
    observer.stop()
    observer.join()
    client.loop_stop()
    client.disconnect()
    logging.debug("MQTT Reports Service stopped.")


def main():
    args = arg_parser()
    configure_logging(args)

    logging.debug("Starting MQTT Reports Service")

    client = set_mqtt_client()
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect

    # Configure reconnect delay and enable logging
    client.reconnect_delay_set(min_delay=30, max_delay=600)
    client.enable_logger()

    observer = None  # Initialize to None for safety

    try:
        # Initial connection
        client.connect(broker, connectport, keepalive)

        # Start MQTT loop in background
        client.loop_start()

        # Setup file monitoring
        observer = setup_watchdog(client)

        # Graceful shutdown on SIGINT/SIGTERM
        def signal_handler(sig, frame):
            stop_services(observer, client)
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Keep the main thread alive
        signal.pause()

    except Exception as e:
        logging.error(f"Error occurred: {e}", exc_info=True)
    finally:
        if observer:
            stop_services(observer, client)


if __name__ == "__main__":
    main()
