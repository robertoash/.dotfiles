"""Command-line interface for Kanata Tools."""

import argparse
import json
import sys

from .config import STATUS_CONFIG
from .layer_switcher import KanataLayerSwitcher
from .status_listener import KanataStatusListener


def main():
    """Main entry point for kanata-tools CLI."""
    parser = argparse.ArgumentParser(
        description="Kanata Tools - Unified tooling for Kanata keyboard remapper",
        prog="kanata-tools"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Switch command
    switch_parser = subparsers.add_parser("switch", help="Switch layers or states")
    switch_group = switch_parser.add_mutually_exclusive_group(required=True)
    switch_group.add_argument("--layout", action="store_true", help="Switch layout (SWE ↔ CMK)")
    switch_group.add_argument("--mod", action="store_true", help="Toggle mod state (MOD ↔ NOMOD)")
    switch_group.add_argument("--toggle", action="store_true", help="Toggle mod state (alias for --mod)")
    
    # Set command
    set_parser = subparsers.add_parser("set", help="Set specific layer")
    set_parser.add_argument("--layout", choices=["swe", "cmk"], required=True, help="Set layout")
    set_parser.add_argument("--mod", choices=["mod", "nomod"], required=True, help="Set mod state")
    
    # Status command
    subparsers.add_parser("status", help="Show current status")
    
    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize on Kanata start")
    init_parser.add_argument(
        "--fresh-start",
        action="store_true",
        help="Force default state (SWE-MOD) ignoring saved state"
    )
    
    # Listen command
    subparsers.add_parser("listen", help="Run status listener daemon")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if args.command == "switch":
        switcher = KanataLayerSwitcher()
        if args.layout:
            switcher.switch_layout()
        elif args.mod or args.toggle:
            switcher.toggle_mod_state()
    
    elif args.command == "set":
        switcher = KanataLayerSwitcher()
        if not switcher.set_specific_layer(args.layout, args.mod):
            sys.exit(1)
    
    elif args.command == "status":
        switcher = KanataLayerSwitcher()
        layout, mod_state = switcher.get_current_state()
        key = (layout, mod_state)
        status = STATUS_CONFIG[key]
        print(json.dumps(status))
    
    elif args.command == "init":
        switcher = KanataLayerSwitcher()
        if args.fresh_start:
            # Force default state
            if not switcher.set_specific_layer("swe", "mod"):
                sys.exit(1)
        else:
            # Smart init based on reboot detection
            if not switcher.initialize_on_start():
                sys.exit(1)
    
    elif args.command == "listen":
        listener = KanataStatusListener()
        listener.run()


if __name__ == "__main__":
    main()