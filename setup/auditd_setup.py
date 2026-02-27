"""
Setup auditd with trycli execve tracking rules.
"""

import subprocess
from pathlib import Path


def setup_auditd(dotfiles_dir):
    """Install trycli audit rules and ensure auditd is running."""
    print("\n🔍 Step: Setting up auditd for trycli usage tracking...")

    rules_source = dotfiles_dir / "system" / "audit" / "rules.d" / "trycli.rules"
    rules_target = Path("/etc/audit/rules.d/trycli.rules")

    if not rules_source.exists():
        print("  ℹ️  No trycli.rules found, skipping")
        return

    # Install rules file if missing or outdated
    needs_update = True
    try:
        if rules_target.exists():
            if rules_source.read_text() == rules_target.read_text():
                needs_update = False
                print("  ✅ trycli.rules already up to date")
    except PermissionError:
        pass

    if needs_update:
        print("  📋 Installing trycli.rules to /etc/audit/rules.d/...")
        result = subprocess.run(
            ["sudo", "install", "-m", "0640", str(rules_source), str(rules_target)]
        )
        if result.returncode != 0:
            print("  ❌ Failed to install trycli.rules")
            return
        print("  ✅ Installed trycli.rules")

    # Enable and start auditd
    is_active = subprocess.run(
        ["systemctl", "is-active", "--quiet", "auditd"]
    ).returncode == 0
    is_enabled = subprocess.run(
        ["systemctl", "is-enabled", "--quiet", "auditd"]
    ).returncode == 0

    if not is_enabled:
        print("  ▶️  Enabling auditd...")
        subprocess.run(["sudo", "systemctl", "enable", "auditd"])

    if not is_active:
        print("  ▶️  Starting auditd...")
        result = subprocess.run(["sudo", "systemctl", "start", "auditd"])
        if result.returncode == 0:
            print("  ✅ auditd started")
        else:
            print("  ❌ Failed to start auditd")
        return

    # Already running — reload rules
    print("  🔄 Reloading audit rules...")
    result = subprocess.run(["sudo", "augenrules", "--load"])
    if result.returncode == 0:
        print("  ✅ Audit rules reloaded")
    else:
        print("  ⚠️  augenrules --load failed")
