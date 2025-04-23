#!/usr/bin/env python3
import json
import subprocess

# Bit → Modifier name
MOD_BITS = {
    1: "Shift",
    2: "Lock",
    4: "Ctrl",
    8: "Alt",
    16: "mod2",
    32: "mod3",
    64: "Super",
    128: "AltGr",
}

MOUSE_KEYCODES = {
    "272": "L",
    "273": "R",
    "274": "M",
}

# Special combos → Alias name
MOD_ALIASES = {
    frozenset(["Super", "Ctrl", "Alt", "Shift"]): "Hyper",
}

MOD_ORDER = ["Hyper", "Super", "Ctrl", "Alt", "Shift", "AltGr"]


def get_mods(modmask: int) -> str:
    # Find active mods
    active_raw = [name for bit, name in MOD_BITS.items() if modmask & bit]
    active_set = frozenset(active_raw)

    # Replace with alias if match found
    for combo, alias in MOD_ALIASES.items():
        if combo.issubset(active_set):
            # Drop implied mods
            active_set = (active_set - combo) | {alias}
            break

    return "+".join([mod for mod in MOD_ORDER if mod in active_set])


def fetch_keybinds() -> list:
    result = subprocess.run(["hyprctl", "binds", "-j"], capture_output=True, text=True)
    return json.loads(result.stdout)


def format_keybinds(binds: list) -> list:
    entries = []
    for b in binds:
        if not b["has_description"]:
            continue

        mods = get_mods(b["modmask"])

        if str(b["key"]).startswith("mouse:"):
            actual_key = b["key"].split(":")[1]
            mapped = MOUSE_KEYCODES.get(actual_key)
            key = f"m:{mapped}" if mapped else f"m:{actual_key}"

        else:
            key = b["key"]

        combo = f"{mods}+{key}" if mods else key
        entries.append(f"[{combo}] {b['description']}")

    print(f"Total entries: {len(entries)}")
    for entry in entries:
        if "Pin window" in entry:
            print("FOUND PIN:", entry)

    return entries


def launch_rofi(entries: list):
    rofi = subprocess.run(
        ["rofi", "-dmenu", "-i", "-p", "Hyprland Binds"],
        input="\n".join(sorted(entries)),
        text=True,
        capture_output=True,
    )
    print(rofi.stdout.strip())


if __name__ == "__main__":
    binds = fetch_keybinds()
    formatted = format_keybinds(binds)
    launch_rofi(formatted)
