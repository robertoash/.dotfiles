#!/usr/bin/env python3

import logging
import os
import signal
import sys

import paho.mqtt.client as mqtt  # pip install paho-mqtt
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

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


def publish_file_contents(file_path):
    topic = file_to_topic.get(file_path)
    if topic:
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


# Event handler for file changes
class FileChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path in file_to_topic:
            logging.info(f"Detected change in {event.src_path}")
            publish_file_contents(event.src_path)


# Graceful shutdown of services
def stop_services(observer, client):
    logging.info("Shutting down services...")
    observer.stop()
    observer.join()
    client.loop_stop()
    client.disconnect()
    logging.info("MQTT Reports Service stopped.")


if __name__ == "__main__":
    logging.info("Starting MQTT Reports Service")

    # Connect to the MQTT broker
    client.connect(broker, connectport, keepalive)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.loop_start()

    # Setup watchdog observer
    event_handler = FileChangeHandler()
    observer = Observer()

    for file_path in file_to_topic.keys():
        dir_path = os.path.dirname(file_path)
        observer.schedule(event_handler, path=dir_path, recursive=False)
        logging.info(f"Watchdog setup and monitoring directory: {dir_path}")

    observer.start()
    logging.info("Watchdog is now waiting for file changes...")

    # Setup signal handler for graceful shutdown
    def signal_handler(sig, frame):
        stop_services(observer, client)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Keep the main thread running indefinitely, allowing the observer and MQTT to run
        signal.pause()  # Blocks until a signal is received
    except Exception as e:
        logging.error(f"Error occurred: {e}")
        stop_services(observer, client)
