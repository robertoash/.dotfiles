#!/usr/bin/env python3
import subprocess
import sys

import requests


def get_mullvad_status():
    try:
        return subprocess.check_output(["mullvad", "status"], text=True)
    except subprocess.CalledProcessError as e:
        return f"Error: {e}"
    except FileNotFoundError:
        return "Error: mullvad command not found"


def get_external_ip():
    try:
        return requests.get("http://api.ipify.org/?format=text").text.strip()
    except requests.RequestException:
        return "unavailable"


def vpn_is_up(mullvad_status):
    return "Connected" in mullvad_status


try:
    mullvad_status = get_mullvad_status()
    extern_ip = get_external_ip()

    if "Error:" in mullvad_status:
        print(f'{{"text": "?", "tooltip": "{mullvad_status}", "class": "vpn-error"}}')
    elif vpn_is_up(mullvad_status):
        print(
            f'{{"text": "󰕥", "tooltip": "connected. ip is {extern_ip}", "class": "vpn-connected"}}'
        )
    else:
        print(
            f'{{"text": "", "tooltip": "disconnected. ip is {extern_ip}", "class": "vpn-disconnected"}}'
        )
except Exception as e:
    print(f'{{"text": "!", "tooltip": "Script error: {str(e)}", "class": "vpn-error"}}')

sys.stdout.flush()
