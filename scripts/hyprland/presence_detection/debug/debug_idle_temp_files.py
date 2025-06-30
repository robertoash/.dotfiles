#!/usr/bin/env python3

import time
from datetime import datetime

files = [
    "/tmp/mqtt/linux_mini_status",
    "/tmp/mqtt/idle_detection_status",
    "/tmp/mqtt/face_presence",
    "/tmp/mqtt/in_office_status",
]


def read_file(path):
    try:
        with open(path, "r") as f:
            return f.read().strip()
    except Exception:
        return "NOT_FOUND"


try:
    while True:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for file in files:
            content = read_file(file)
            print(f"{timestamp} {file}: {content}")
        time.sleep(1)
except KeyboardInterrupt:
    pass
