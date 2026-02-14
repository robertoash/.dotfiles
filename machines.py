#!/usr/bin/env python3
"""
Machine-specific configuration.
Define machine properties and flags here.
"""

import socket

# Machine configurations
MACHINES = {
    "workmbp": {
        "is_macos": True,
        "is_linux": False,
        "is_server": False,
    },
    "linuxmini": {
        "is_macos": False,
        "is_linux": True,
        "is_server": False,
    },
    "oldmbp": {
        "is_macos": False,
        "is_linux": True,
        "is_server": False,
    },
    "thor": {
        "is_macos": False,
        "is_linux": True,
        "is_server": True,
    },
}


def get_machine_config(hostname=None):
    """
    Get configuration for a machine.
    Returns a config dict with flags, or a default config for unknown machines.

    Args:
        hostname: Machine hostname. If None, uses current hostname.

    Returns:
        dict: Machine configuration with flags
    """
    if hostname is None:
        hostname = socket.gethostname()

    # Return machine-specific config if it exists
    if hostname in MACHINES:
        return MACHINES[hostname]

    # Default config for unknown machines - detect platform
    import platform
    system = platform.system().lower()

    return {
        "is_macos": system == "darwin",
        "is_linux": system == "linux",
        "is_server": False,
    }
