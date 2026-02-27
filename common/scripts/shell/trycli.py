#!/usr/bin/env python3
"""trycli - Browse recently installed CLI tools with fzf."""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from collections import Counter, namedtuple
from datetime import datetime
from pathlib import Path

CACHE_FILE = Path.home() / ".cache" / "trycli" / "packages.tsv"
CACHE_TTL = 86400  # 24 hours

Package = namedtuple("Package", ["epoch", "name", "source", "description"])


# --- Collectors ---

def collect_pacman():
    if not shutil.which("pacman"):
        return []

    try:
        explicit = subprocess.run(
            ["pacman", "-Qqet"], capture_output=True, text=True, check=True
        ).stdout.strip().splitlines()
    except subprocess.CalledProcessError:
        return []

    if not explicit:
        return []

    try:
        info = subprocess.run(
            ["pacman", "-Qi"] + explicit, capture_output=True, text=True, check=True
        ).stdout
    except subprocess.CalledProcessError:
        return []

    packages = []
    current = {}
    for line in info.splitlines():
        if line.startswith("Name "):
            current = {}
            current["name"] = line.split(":", 1)[1].strip()
        elif line.startswith("Description "):
            current["description"] = line.split(":", 1)[1].strip()
        elif line.startswith("Install Date"):
            date_str = line.split(":", 1)[1].strip()
            try:
                # e.g. "Thu 01 Feb 2024 10:23:45 AM UTC"
                epoch = int(datetime.strptime(date_str, "%a %d %b %Y %I:%M:%S %p %Z").timestamp())
            except ValueError:
                try:
                    epoch = int(datetime.strptime(date_str, "%a %d %b %Y %H:%M:%S %Z").timestamp())
                except ValueError:
                    epoch = 0
            current["epoch"] = epoch
        elif line == "" and "name" in current:
            if shutil.which(current["name"]):
                packages.append(Package(
                    epoch=current.get("epoch", 0),
                    name=current["name"],
                    source="pacman",
                    description=current.get("description", ""),
                ))
            current = {}

    return packages


def collect_brew():
    if not shutil.which("brew"):
        return []

    try:
        result = subprocess.run(
            ["brew", "info", "--json=v2", "--installed"],
            capture_output=True, text=True, check=True
        )
    except subprocess.CalledProcessError:
        return []

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []

    packages = []
    for formula in data.get("formulae", []):
        installed = formula.get("installed", [])
        if not installed:
            continue
        if not formula.get("installed_on_request", False):
            continue

        name = formula.get("name", "")
        desc = formula.get("desc", "")
        epoch = installed[-1].get("time", 0) or 0

        if shutil.which(name):
            packages.append(Package(epoch=epoch, name=name, source="brew", description=desc))

    return packages


def collect_cargo():
    if not shutil.which("cargo"):
        return []

    try:
        result = subprocess.run(
            ["cargo", "install", "--list"],
            capture_output=True, text=True, check=True
        )
    except subprocess.CalledProcessError:
        return []

    cargo_bin = Path.home() / ".cargo" / "bin"
    packages = []
    current_crate = None

    for line in result.stdout.splitlines():
        if not line.startswith(" ") and line.strip():
            # e.g. "ripgrep v14.1.0:"
            parts = line.strip().rstrip(":").rsplit(" v", 1)
            current_crate = parts[0].strip() if parts else line.strip()
        elif line.startswith("    ") and current_crate:
            # e.g. "    rg"
            binary = line.strip()
            bin_path = cargo_bin / binary
            if bin_path.exists():
                epoch = int(os.path.getmtime(bin_path))
                if shutil.which(binary):
                    packages.append(Package(
                        epoch=epoch,
                        name=binary,
                        source="cargo",
                        description=f"from crate {current_crate}",
                    ))

    return packages


# --- Cache ---

def load_cache():
    if not CACHE_FILE.exists():
        return None
    age = time.time() - CACHE_FILE.stat().st_mtime
    if age > CACHE_TTL:
        return None
    packages = []
    with open(CACHE_FILE) as f:
        for line in f:
            parts = line.rstrip("\n").split("\t", 3)
            if len(parts) == 4:
                packages.append(Package(
                    epoch=int(parts[0]),
                    name=parts[1],
                    source=parts[2],
                    description=parts[3],
                ))
    return packages


def save_cache(packages):
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        for p in packages:
            f.write(f"{p.epoch}\t{p.name}\t{p.source}\t{p.description}\n")


def build_packages():
    all_packages = []
    seen = set()
    for pkg in collect_pacman() + collect_brew() + collect_cargo():
        if pkg.name not in seen:
            seen.add(pkg.name)
            all_packages.append(pkg)
    all_packages.sort(key=lambda p: p.epoch, reverse=True)
    return all_packages


# --- Atuin usage counts ---

def get_atuin_counts():
    if not shutil.which("atuin"):
        return Counter()
    try:
        result = subprocess.run(
            ["atuin", "history", "list", "--cmd-only"],
            capture_output=True, text=True, timeout=10
        )
        counts = Counter()
        for line in result.stdout.splitlines():
            cmd = line.strip().split()[0] if line.strip() else ""
            if cmd:
                counts[cmd] += 1
        return counts
    except (subprocess.TimeoutExpired, Exception):
        return Counter()


# --- fzf ---

def format_line(pkg, counts):
    name_col = pkg.name.ljust(28)
    source_col = f"({pkg.source})".ljust(10)
    uses = counts.get(pkg.name, 0)
    uses_col = f"[{uses} uses]".ljust(12)
    desc = pkg.description[:60] if pkg.description else ""
    date_str = datetime.fromtimestamp(pkg.epoch).strftime("%Y-%m-%d") if pkg.epoch else "unknown   "
    return f"{date_str}  {name_col}{source_col}{uses_col}  {desc}"


def run_fzf(packages, counts):
    if not packages:
        print("No CLI tools found.", file=sys.stderr)
        sys.exit(1)

    if not shutil.which("fzf"):
        print("fzf not found in PATH.", file=sys.stderr)
        sys.exit(1)

    lines = [format_line(p, counts) for p in packages]
    fzf_input = "\n".join(lines)

    preview_cmd = (
        "tool=$(echo {} | awk '{print $3}'); "
        "$tool --help 2>&1 | head -80 || echo 'No --help available for '$tool"
    )

    fzf_cmd = [
        "fzf",
        "--ansi",
        "--header", "DATE        NAME                         SOURCE    USES          DESCRIPTION",
        "--preview", preview_cmd,
        "--preview-window", "right:60%:wrap",
        "--bind", "ctrl-/:toggle-preview",
    ]

    try:
        result = subprocess.run(
            fzf_cmd,
            input=fzf_input,
            capture_output=True,
            text=True,
        )
    except KeyboardInterrupt:
        sys.exit(0)

    if result.returncode != 0:
        sys.exit(0)

    selected = result.stdout.strip()
    if not selected:
        sys.exit(0)

    # Extract tool name (3rd field, after date and spaces)
    tool_name = selected.split()[2] if len(selected.split()) >= 3 else selected.split()[0]
    tool_path = shutil.which(tool_name)

    if not tool_path:
        print(f"Tool '{tool_name}' not found in PATH.", file=sys.stderr)
        sys.exit(1)

    help_output = subprocess.run(
        [tool_path, "--help"], capture_output=True, text=True
    )
    text = help_output.stdout or help_output.stderr

    pager = shutil.which("less") or shutil.which("more")
    if pager and sys.stdout.isatty():
        subprocess.run([pager, "-R"], input=text, text=True)
    else:
        print(text)


# --- Main ---

def main():
    parser = argparse.ArgumentParser(description="Browse recently installed CLI tools")
    parser.add_argument("-r", "--refresh", action="store_true", help="Force rebuild cache")
    parser.add_argument("--stdout", action="store_true", help="Print package list to stdout (for scripting)")
    args = parser.parse_args()

    if args.refresh or (packages := load_cache()) is None:
        print("Scanning installed packages...", file=sys.stderr)
        packages = build_packages()
        save_cache(packages)
        print(f"Found {len(packages)} CLI tools.", file=sys.stderr)

    if args.stdout:
        counts = get_atuin_counts()
        for p in packages:
            print(format_line(p, counts))
        return

    counts = get_atuin_counts()
    run_fzf(packages, counts)


if __name__ == "__main__":
    main()
