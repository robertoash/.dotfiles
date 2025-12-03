#!/usr/bin/env python3

import argparse
import subprocess
import sys

from .cookie_ops import (
    bake_cookie,
    eat_cookie,
    get_all_cookies,
    get_sweet_cookies,
    puke_cookie,
)
from .table_ops import table_up, table_down, get_kitchen_status

FZF = "/usr/bin/fzf"
FZF_STYLE = ["--height=30%", "--reverse", "--prompt"]


def fzf_prompt(prompt_text, options):
    result = subprocess.run(
        [FZF, *FZF_STYLE, prompt_text],
        input="\n".join(options),
        text=True,
        capture_output=True,
    )
    return result.stdout.strip()


def fzf_input(prompt_text):
    result = subprocess.run(
        [FZF, *FZF_STYLE, prompt_text, "--print-query"],
        input="",
        text=True,
        capture_output=True,
    )
    return result.stdout.strip()


def run_tui():
    """Run the TUI version of the application."""
    try:
        action = fzf_prompt(
            "Choose an action > ",
            [
                "Eat a Cookie 🍪",
                "Puke a Cookie 🤢",
                "Bake a Cookie 🍽️",
                "Peek in the Kitchen 👁️",
                "Close the Jar 🔒",
            ],
        )

        if action == "Close the Jar 🔒" or not action:
            sys.exit(0)

        if action == "Peek in the Kitchen 👁️":
            get_kitchen_status()
            return

        cookie_name = fzf_input("Which 🍪? >")
        if not cookie_name:
            print("No 🍪 entered.")
            return

        execute_action(action, cookie_name)

    except KeyboardInterrupt:
        print("\nJar closed.")
    except Exception as e:
        print(f"💥 Something smells rotten in the jar: {e}")


def execute_action(action, cookie_name, **kwargs):
    """Execute the specified action with the given cookie name."""
    match action:
        case "Eat a Cookie 🍪" | "eat":
            eat_cookie(cookie_name)
        case "Puke a Cookie 🤢" | "puke":
            # Handle special puke options
            if kwargs.get("sweet"):
                sweet_cookies = get_sweet_cookies()
                if not sweet_cookies:
                    print("🍪 No sweet cookies found in the jar.")
                    return
                print(f"🤢 Puking sweet cookies: {', '.join(sweet_cookies)}")
                for cookie in sweet_cookies:
                    try:
                        puke_cookie(cookie)
                        print(f"✅ Puked {cookie}")
                    except Exception as e:
                        print(f"❌ Failed to puke {cookie}: {e}")
            elif kwargs.get("all"):
                all_cookies = get_all_cookies()
                if not all_cookies:
                    print("🍪 No cookies found in the jar.")
                    return
                print(f"🤢 Puking all cookies: {', '.join(all_cookies)}")
                for cookie in all_cookies:
                    try:
                        puke_cookie(cookie)
                        print(f"✅ Puked {cookie}")
                    except Exception as e:
                        print(f"❌ Failed to puke {cookie}: {e}")
            else:
                puke_cookie(cookie_name)
        case "Bake a Cookie 🍽️" | "bake":
            bake_cookie(cookie_name)
        case _:
            print("Invalid selection.")


def main():
    parser = argparse.ArgumentParser(
        description="Cookie Jar - Manage your cookies 🍪", prog="cjar"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Eat command
    eat_parser = subparsers.add_parser("eat", help="Eat a cookie 🍪")
    eat_parser.add_argument("cookie_name", help="Name of the cookie to eat")

    # Puke command
    puke_parser = subparsers.add_parser("puke", help="Puke a cookie 🤢")
    puke_group = puke_parser.add_mutually_exclusive_group(required=True)
    puke_group.add_argument("cookie_name", nargs="?", help="Name of the cookie to puke")
    puke_group.add_argument(
        "--sweet", action="store_true", help="Puke all sweet cookies (vanilla, lime)"
    )
    puke_group.add_argument(
        "--all", action="store_true", help="Puke all registered cookies"
    )

    # Bake command
    bake_parser = subparsers.add_parser("bake", help="Bake a cookie 🍽️")
    bake_parser.add_argument("cookie_name", help="Name of the cookie to bake")
    
    # Table command
    table_parser = subparsers.add_parser("table", help="Set or clear the table 🍽️")
    table_subparsers = table_parser.add_subparsers(dest="table_action", help="Table actions")
    
    # Table up
    table_up_parser = table_subparsers.add_parser("up", help="Set the table for the feast")
    table_up_parser.add_argument(
        "-f", "--file",
        help="Path to table setup (default: ~/.config/cjar/plates/vanilla/pantry/table.yml)",
        dest="table_setup"
    )
    
    # Table down
    table_down_parser = table_subparsers.add_parser("down", help="Clear the table after the feast")
    table_down_parser.add_argument(
        "-f", "--file",
        help="Path to compose file (default: ~/.config/cjar/pantry/table.yml)",
        dest="table_setup"
    )

    # Feast command
    feast_parser = subparsers.add_parser("feast", help="Full feast operations 🍽️")
    feast_subparsers = feast_parser.add_subparsers(dest="feast_action", help="Feast actions")
    
    # Feast now
    feast_now_parser = feast_subparsers.add_parser("now", help="Begin the feast")
    feast_now_parser.add_argument(
        "-f", "--file",
        help="Path to table setup",
        dest="table_setup"
    )
    
    # Feast done
    feast_done_parser = feast_subparsers.add_parser("done", help="End the feast")
    feast_done_parser.add_argument(
        "-f", "--file",
        help="Path to table setup",
        dest="table_setup"
    )

    # Peek command
    peek_parser = subparsers.add_parser("peek", help="Peek in the kitchen 👁️")

    args = parser.parse_args()

    # If no command is provided, run TUI
    if not args.command:
        run_tui()
        return

    # Execute command-line operation
    try:
        if args.command == "feast":
            if args.feast_action == "now":
                eat_cookie("vanilla")
                table_up(args.table_setup)
            elif args.feast_action == "done":
                table_down(args.table_setup)
                puke_cookie("vanilla")
            else:
                feast_parser.print_help()
        elif args.command == "table":
            if args.table_action == "up":
                table_up(args.table_setup)
            elif args.table_action == "down":
                table_down(args.table_setup)
            else:
                table_parser.print_help()
        elif args.command == "peek":
            get_kitchen_status()
        elif args.command == "puke":
            execute_action(
                args.command, args.cookie_name, sweet=args.sweet, all=args.all
            )
        else:
            execute_action(args.command, args.cookie_name)
    except Exception as e:
        print(f"💥 Something smells rotten in the jar: {e}")
        sys.exit(1)
