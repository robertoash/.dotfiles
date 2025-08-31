#!/usr/bin/env python3

"""
Simplified Rofi Domain History Browser for qutebrowser
Shows only root domains from history with numbered indices

Usage:
    rofi_history_browser [current|new]

Arguments:
    current  - Open in current tab (default)
    new      - Open in new tab
"""

import os
import sys
import sqlite3
import subprocess
import re
from urllib.parse import urlparse
from collections import Counter


def extract_domain(url):
    """Extract root domain from URL."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc
        
        # Skip empty domains
        if not domain:
            return None
            
        # For localhost entries, include the port if present
        if domain.startswith("localhost") or domain.startswith("127.0.0.1"):
            return domain  # Keep localhost:3000, localhost:8080, etc. as separate entries
            
        # Remove www. prefix if present for other domains
        if domain.startswith("www."):
            domain = domain[4:]
            
        return domain
    except (ValueError, AttributeError):
        return None


def ensure_protocol(url):
    """Add appropriate protocol if not present."""
    if not url.startswith(("http://", "https://")):
        # Use http for localhost, https for everything else
        if url.startswith("localhost") or url.startswith("127.0.0.1"):
            return f"http://{url}"
        else:
            return f"https://{url}"
    return url


def get_domain_history():
    """Get unique domains from qutebrowser history, sorted by frequency."""
    data_dir = os.environ.get("QUTE_DATA_DIR", "")
    if not data_dir:
        print("ERROR: QUTE_DATA_DIR not set", file=sys.stderr)
        sys.exit(1)

    history_db = os.path.join(data_dir, "history.sqlite")
    if not os.path.exists(history_db):
        print(f"ERROR: History database not found: {history_db}", file=sys.stderr)
        sys.exit(1)

    try:
        conn = sqlite3.connect(history_db)
        cursor = conn.cursor()

        # Get all URLs from history
        cursor.execute("SELECT url FROM CompletionHistory")
        urls = cursor.fetchall()
        conn.close()

        # Extract domains and count frequency, filtering out None values
        domains = []
        for url in urls:
            if url[0]:
                domain = extract_domain(url[0])
                if domain:  # Only add non-None domains
                    domains.append(domain)
        
        domain_counts = Counter(domains)

        # Return all domains sorted by frequency
        top_domains = [domain for domain, _ in domain_counts.most_common()]
        return top_domains

    except sqlite3.Error as e:
        print(f"ERROR: Database error: {e}", file=sys.stderr)
        sys.exit(1)


def show_rofi_menu(domains):
    """Display domains in rofi with numbered indices."""
    # Create numbered entries
    numbered_entries = []
    for i, domain in enumerate(domains, 1):
        numbered_entries.append(f"{i:02d}: {domain}")

    # Join entries with newlines
    rofi_input = "\n".join(numbered_entries)

    # Launch rofi
    try:
        result = subprocess.run(
            [
                "rofi",
                "-dmenu",
                "-i",
                "-l",
                "20",
                "-p",
                "History Domains",
                "-format",
                "i:s",  # Return both index and string
                "-kb-accept-entry",
                "Return",
                "-kb-accept-alt",
                "Alt+Return",
                "-kb-custom-1",
                "Alt+d",  # Custom binding for delete
                "-mesg",
                "Enter: Open | Alt+D: Delete domain history",
                "-no-custom",
            ],
            input=rofi_input,
            text=True,
            capture_output=True,
        )

        # Return code 10 = custom-1 (Ctrl+D)
        if result.returncode == 10:
            return ("delete", result.stdout.strip())
        elif result.returncode == 0:
            return ("open", result.stdout.strip())
        else:
            sys.exit(0)  # User cancelled

    except FileNotFoundError:
        print("ERROR: rofi not found. Please install rofi.", file=sys.stderr)
        sys.exit(1)
    except subprocess.SubprocessError as e:
        print(f"ERROR: rofi failed: {e}", file=sys.stderr)
        sys.exit(1)


def delete_domain_history(domain):
    """Delete all history entries containing the domain string."""
    data_dir = os.environ.get("QUTE_DATA_DIR", "")
    if not data_dir:
        print("ERROR: QUTE_DATA_DIR not set", file=sys.stderr)
        return False

    history_db = os.path.join(data_dir, "history.sqlite")
    if not os.path.exists(history_db):
        print(f"ERROR: History database not found: {history_db}", file=sys.stderr)
        return False

    try:
        conn = sqlite3.connect(history_db)
        cursor = conn.cursor()
        
        # Simply delete all URLs containing this domain string
        pattern = f"%{domain}%"
        
        cursor.execute("DELETE FROM History WHERE url LIKE ?", (pattern,))
        deleted_history = cursor.rowcount
        
        cursor.execute("DELETE FROM CompletionHistory WHERE url LIKE ?", (pattern,))
        deleted_completion = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        total_deleted = deleted_history + deleted_completion
        print(f"Deleted {total_deleted} entries for domain '{domain}' (History: {deleted_history}, Completion: {deleted_completion})", file=sys.stderr)
        return True
        
    except sqlite3.Error as e:
        print(f"ERROR: Database error during deletion: {e}", file=sys.stderr)
        return False


def send_to_qutebrowser(url, new_tab=False):
    """Send open command to qutebrowser."""
    fifo_path = os.environ.get("QUTE_FIFO", "")

    # Build command
    if new_tab:
        cmd = f"open -t {url}"
    else:
        cmd = f"open {url}"

    # Debug: Print what we're trying to send (comment out when working)
    # print(f"DEBUG: Sending command: {cmd}", file=sys.stderr)
    # print(f"DEBUG: FIFO path: {fifo_path}", file=sys.stderr)

    # Try to send via FIFO first
    if fifo_path and os.path.exists(fifo_path):
        try:
            with open(fifo_path, "w") as fifo:
                fifo.write(cmd + "\n")
                fifo.flush()
            # print(f"DEBUG: Command sent successfully via FIFO", file=sys.stderr)
            return
        except OSError as e:
            # print(f"DEBUG: FIFO write failed: {e}", file=sys.stderr)
            pass

    # Fallback: launch new qutebrowser instance
    # print("DEBUG: Falling back to launching new qutebrowser instance", file=sys.stderr)
    try:
        subprocess.run(["qutebrowser", url], check=False)
    except FileNotFoundError:
        print("ERROR: Could not communicate with qutebrowser", file=sys.stderr)
        sys.exit(1)


def main():
    # Parse arguments
    tab_mode = sys.argv[1] if len(sys.argv) > 1 else "current"
    new_tab = tab_mode == "new"

    while True:  # Loop to allow reopening after deletion
        # Get domain history
        domains = get_domain_history()
        if not domains:
            print("No domains found in history", file=sys.stderr)
            sys.exit(1)

        # Show rofi menu
        result = show_rofi_menu(domains)
        if not result:
            sys.exit(0)

        action, selected = result
        
        # Parse the selection - it now comes as "index:string"
        # Extract just the string part after the colon
        if ":" in selected:
            # Split on first colon to get the domain part
            parts = selected.split(":", 1)
            if len(parts) > 1:
                selected = parts[1].strip()
        
        # Extract domain from selected entry (remove number prefix if present)
        domain_match = re.match(r"^(?:\d+:\s*)?(.+)$", selected)
        if not domain_match:
            print(f"ERROR: Invalid selection format: {selected}", file=sys.stderr)
            sys.exit(1)

        domain = domain_match.group(1).strip()
        
        if action == "delete":
            # Delete the domain history
            if delete_domain_history(domain):
                # Continue the loop to reopen rofi
                continue
            else:
                print(f"Failed to delete history for {domain}", file=sys.stderr)
                sys.exit(1)
        else:
            # Open the URL
            url = ensure_protocol(domain)
            send_to_qutebrowser(url, new_tab)
            break  # Exit after opening


if __name__ == "__main__":
    main()
