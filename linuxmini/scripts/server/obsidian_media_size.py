#!/usr/bin/env python3

import subprocess
from datetime import datetime

# File path to write the output
output_file = "/home/rash/obsidian/vault/Dev/Server/Offline/Current Media Size.md"

# Command to execute
command = [
    "ssh",
    "offlinelab",
    (
        "du --all --max-depth=2 -h /media/offline_data/data/media/ | sort -rh | "
        'awk \'NR==1 {sub(/\\/media\\/offline_data\\/data\\/media\\//, ""); '
        'printf "%-6s %-s\\n", "TOTAL", $1; next} '
        '{gsub(/\\/media\\/offline_data\\/data\\/media\\//, ""); '
        'gsub(/[ ()]/, "_"); $2 = tolower($2); gsub(/__+/, "_", $2); gsub(/_$/, "", $2); '
        'printf "%-6s %-s\\n", $1, $2}\''
    ),
]

try:
    # Execute the command and capture the output
    result = subprocess.run(
        command,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    output = result.stdout.strip()
except subprocess.CalledProcessError as e:
    output = f"Error: {e.stderr.strip()}"

# Create markdown content
current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
markdown_content = f"Last updated: {current_time}\n\n```\n{output}\n```"

# Write to the output file
with open(output_file, "w") as file:
    file.write(markdown_content)
