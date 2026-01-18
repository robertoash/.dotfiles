#!/usr/bin/env python3

import argparse
import logging
import os
import sys
import threading
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
    "/tmp/mqtt/idle_detection_status": "scripts/idle_detection/status",
    "/tmp/mqtt/manual_override_status": "scripts/idle_detection/manual_override",
}

# Store previous contents
previous_contents = {}

# MQTT connection parameters
clientname = "linux_mini_mqtt_reports"
broker = "10.20.10.100"
connectport = 1883
keepalive = 60

# Broker status monitoring
BROKER_STATUS_TOPIC = "homeassistant/status"  # Home Assistant's broker status topic
broker_online = False

# Reconnection control
reconnecting = False
reconnect_lock = threading.Lock()
RECONNECT_DELAY = 5  # seconds between reconnection attempts


def ensure_files_exist():
    """Ensure all required files exist with proper permissions."""
    os.makedirs("/tmp/mqtt", exist_ok=True)
    for file_path in file_to_topic.keys():
        if not os.path.exists(file_path):
            with open(file_path, "w") as f:
                f.write("")  # Create empty file
            logging.info(f"Created empty file: {file_path}")
        else:
            with open(file_path, "r") as f:
                content = f.read().strip()
                logging.info(f"Existing file {file_path} contains: '{content}'")

        # Ensure file has valid content
        with open(file_path, "r") as f:
            content = f.read().strip()
            if "webcam" in file_path and (
                not content or content not in ["active", "inactive"]
            ):
                content = "inactive"
            elif "mini" in file_path and (
                not content or content not in ["active", "inactive"]
            ):
                content = "inactive"
            elif "idle_detection_status" in file_path and (
                not content or content not in ["in_progress", "inactive"]
            ):
                content = "inactive"
            elif "manual_override_status" in file_path and (
                not content or content not in ["active", "inactive"]
            ):
                content = "inactive"
        with open(file_path, "w") as f:
            f.write(content)
        logging.info(f"Initialized empty file {file_path} with content: '{content}'")

        os.chmod(file_path, 0o644)  # Ensure proper permissions


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
    logging.debug("Creating MQTT client...")
    client = mqtt.Client(client_id=clientname)
    logging.debug(f"Setting credentials for user: {os.environ['mqtt_user']}")
    client.username_pw_set(
        username=os.environ["mqtt_user"], password=os.environ["mqtt_password"]
    )
    logging.debug("Setting will message...")
    client.will_set(
        "devices/" + clientname + "/status", payload="offline", qos=1, retain=True
    )
    logging.info("MQTT client created successfully")
    return client


def safe_reconnect(client):
    global reconnecting
    with reconnect_lock:
        if reconnecting:
            logging.debug("Reconnection already in progress, skipping...")
            return
        reconnecting = True
        try:
            logging.info("Attempting to reconnect...")
            client.reconnect()
            logging.debug(
                f"Waiting {RECONNECT_DELAY} seconds for connection to establish..."
            )
            time.sleep(RECONNECT_DELAY)
            logging.info("Reconnection attempt completed")
        except Exception as e:
            logging.error(f"Failed to reconnect: {e}", exc_info=True)
            # Don't exit on reconnection failure, let systemd handle restart
            time.sleep(RECONNECT_DELAY)
        finally:
            reconnecting = False
            logging.debug("Reconnection state reset")


def on_connect(client, userdata, flags, rc):
    global broker_online, reconnecting
    logging.debug(f"on_connect called with rc={rc}, flags={flags}")
    if rc == 0:
        logging.info("Connected OK to MQTT broker")
        broker_online = True
        reconnecting = False

        logging.debug(f"Subscribing to {BROKER_STATUS_TOPIC}...")
        sub_result = client.subscribe(BROKER_STATUS_TOPIC, qos=1)
        if sub_result[0] != mqtt.MQTT_ERR_SUCCESS:
            logging.warning(
                f"Failed to subscribe to {BROKER_STATUS_TOPIC}: {mqtt.error_string(sub_result[0])}"
            )
        else:
            logging.debug(f"Subscription result: {sub_result}")

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
    else:
        logging.error(f'Connection failed. Returned code "{rc}"')


def on_disconnect(client, userdata, rc):
    global broker_online
    logging.debug(f"on_disconnect called with rc={rc}")

    if isinstance(rc, mqtt.DisconnectFlags):
        if rc.is_disconnect_packet_from_server:
            logging.warning("Disconnected: Server might be down.")
            broker_online = False
        else:
            logging.warning("Disconnected: Client initiated or other reason.")
    else:
        logging.warning(f"Disconnected for reason {rc}")

    for arg in args:
        if isinstance(arg, mqtt.ReasonCode):
            logging.warning(f"Reason code for disconnection: {arg}")
        elif isinstance(arg, mqtt.Properties):
            logging.debug(f"Disconnection properties: {arg}")
        else:
            logging.warning(f"Unknown argument in on_disconnect: {arg}")

    logging.debug("Publishing offline status...")
    client.publish(
        "devices/" + clientname + "/status", payload="offline", qos=1, retain=True
    )

    logging.info("Initiating safe reconnect...")
    safe_reconnect(client)


def on_message(client, userdata, message):
    global broker_online
    topic = message.topic
    payload = message.payload.decode()
    logging.debug(f"Received message on topic {topic}: {payload}")

    if topic == BROKER_STATUS_TOPIC:
        if payload == "offline" and client.is_connected() and broker_online:
            logging.warning(
                "Broker status changed to offline, updating status and attempting to reconnect"
            )
            broker_online = False
            if not reconnecting:
                logging.info(
                    "Home Assistant broker is offline, attempting to reconnect..."
                )
                safe_reconnect(client)
        elif payload == "online" and not broker_online:
            logging.info("Broker status changed to online")
            broker_online = True


def on_publish(client, userdata, mid):
    logging.debug(f"Publish complete for message id: {mid}")


def publish_file_contents(client, file_path):
    topic = file_to_topic.get(file_path)
    if topic:
        try:
            logging.debug(f"Opening file {file_path} for reading...")
            with open(file_path, "r") as file:
                content = file.read().strip()
                logging.debug(f"File content read: '{content}'")
                logging.debug(f"Previous content: '{previous_contents.get(file_path)}'")
                if content != previous_contents.get(file_path):
                    logging.debug(f"Content changed, preparing to publish to {topic}")
                    logging.debug(
                        f"MQTT client state: connected={client.is_connected()}"
                    )
                    result = client.publish(topic, payload=content, qos=1, retain=True)

                    if result.rc != mqtt.MQTT_ERR_SUCCESS:
                        logging.warning(
                            f"Failed to publish {topic}: {mqtt.error_string(result.rc)}"
                        )
                    else:
                        logging.debug(f"Publish completed with result: {result.rc}")
                        previous_contents[file_path] = content
                        logging.debug("Previous content updated")
                else:
                    logging.debug(f"Content unchanged for {file_path}")
        except FileNotFoundError:
            logging.warning(f"File not found: {file_path}")
        except IOError as e:
            logging.warning(f"Error reading file {file_path}: {e}")
        except Exception as e:
            logging.error(
                f"Unexpected error publishing file contents: {e}", exc_info=True
            )


class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, client):
        self.client = client
        logging.debug("FileChangeHandler initialized")

    def on_modified(self, event):
        logging.debug(f"File system event detected: {event}")
        if event.src_path in file_to_topic:
            logging.debug(f"Processing change in {event.src_path}")
            publish_file_contents(self.client, event.src_path)
        else:
            logging.debug(
                f"Ignoring change in {event.src_path} (not in monitored files)"
            )


def setup_watchdog(client):
    logging.debug("Setting up watchdog...")
    event_handler = FileChangeHandler(client)
    observer = Observer()

    for file_path in file_to_topic.keys():
        dir_path = os.path.dirname(file_path)
        logging.debug(f"Scheduling watchdog for directory: {dir_path}")
        observer.schedule(event_handler, path=dir_path, recursive=False)

    logging.debug("Starting watchdog observer...")
    observer.start()
    logging.debug("Watchdog observer started successfully")
    return observer


def run_file_monitor(client):
    logging.debug("Starting file monitor thread...")
    observer = setup_watchdog(client)
    logging.debug("File monitor thread running, waiting for events...")
    observer.join()


# ----- Main Function -----
def main():
    logging.debug("Script starting...")
    args = arg_parser()
    logging.debug(f"Arguments parsed: {args}")

    configure_logging(args)
    logging.debug("Logging configured")

    logging.debug("Starting MQTT Reports Service")

    logging.debug("Ensuring files exist...")
    ensure_files_exist()
    logging.debug("Files checked")

    logging.debug("Setting up MQTT client...")
    client = set_mqtt_client()
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    client.on_publish = on_publish
    logging.debug("MQTT client setup complete")

    logging.debug("Configuring reconnect delay...")
    client.reconnect_delay_set(min_delay=1, max_delay=300)
    # Note: client.enable_logger() is very verbose and generates excessive logs
    # Only enable for debugging specific MQTT issues
    # logging.debug("Enabling MQTT logger...")
    # client.enable_logger()

    try:
        logging.debug(f"Connecting to MQTT broker at {broker}:{connectport}...")
        client.connect(broker, connectport, keepalive)
        logging.debug("Initial connection established")

        # Start MQTT loop in background
        logging.debug("Starting MQTT loop in background...")
        client.loop_start()

        # Initial publish
        for file_path, topic in file_to_topic.items():
            publish_file_contents(client, file_path)

        # Wait for connection to be established and initial publishes to complete
        logging.debug("Waiting for connection and initial publishes...")
        time.sleep(2)

        # Start watchdog after connection is established
        logging.debug("Starting watchdog thread...")
        watchdog_thread = threading.Thread(
            target=run_file_monitor, args=(client,), daemon=True
        )
        watchdog_thread.start()
        logging.debug("Watchdog thread started")

        # Stay alive in main thread
        logging.debug("Entering main idle loop...")
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        logging.info("MQTT Reports Service interrupted by user")
    except Exception as e:
        logging.error(f"Unhandled error occurred: {e}", exc_info=True)
    finally:
        logging.debug("Shutting down MQTT client...")
        client.loop_stop()
        client.disconnect()
        logging.debug("MQTT client shutdown complete")


if __name__ == "__main__":
    main()
