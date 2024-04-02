#!/usr/bin/env python3
import subprocess

import requests


def get_mullvad_status():
    return subprocess.check_output(["mullvad", "status"], text=True)


def get_external_ip():
    try:
        return requests.get("http://api.ipify.org/?format=text").text.strip()
    except requests.RequestException:
        return "Unavailable"


def vpn_is_up(mullvad_status):
    return "Connected" in mullvad_status


mullvad_status = get_mullvad_status()
extern_ip = get_external_ip()

if vpn_is_up(mullvad_status):
    print(
        f'{{"text": "󰕥", "tooltip": "connected. ip is {extern_ip}", "class": "vpn-connected"}}'
    )
else:
    print(
        f'{{"text": "", "tooltip": "disconnected. ip is {extern_ip}", "class": "vpn-disconnected"}}'
    )
