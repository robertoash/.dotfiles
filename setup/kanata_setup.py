"""
Setup kanata keyboard remapper system service, udev rules, and kanata-tools.
"""

import subprocess
from pathlib import Path


UINPUT_UDEV_RULE = 'KERNEL=="uinput", GROUP="uinput", MODE="0660", OPTIONS+="static_node=uinput"\n'


def _run_sudo(args, input_text=None):
    return subprocess.run(
        ["sudo"] + args,
        input=input_text,
        text=True,
        capture_output=True,
    )


def setup_kanata(dotfiles_dir):
    """Setup kanata system service, udev rules, user groups, and kanata-tools"""
    print("\n⌨️  Setting up kanata...")

    if not Path("/usr/bin/kanata").exists():
        print("  ⚠️  kanata not installed, skipping")
        return

    _setup_groups()
    _setup_udev_rule()
    _setup_tmpfiles(dotfiles_dir)
    _setup_system_service(dotfiles_dir)
    _install_kanata_tools(dotfiles_dir)


def _setup_groups():
    """Add user to input and uinput groups"""
    import grp
    import pwd

    user = "rash"
    needed_groups = ["input", "uinput"]

    # Create uinput group if it doesn't exist
    try:
        grp.getgrnam("uinput")
    except KeyError:
        result = _run_sudo(["groupadd", "--system", "uinput"])
        if result.returncode == 0:
            print("  ✅ Created uinput group")
        else:
            print(f"  ⚠️  Failed to create uinput group: {result.stderr.strip()}")
            return

    # Check current group membership
    try:
        user_info = pwd.getpwnam(user)
        current_groups = [g.gr_name for g in grp.getgrall() if user in g.gr_mem]
        current_groups.append(grp.getgrgid(user_info.pw_gid).gr_name)
    except KeyError:
        current_groups = []

    for group in needed_groups:
        if group not in current_groups:
            result = _run_sudo(["usermod", "-aG", group, user])
            if result.returncode == 0:
                print(f"  ✅ Added {user} to {group} group (re-login required)")
            else:
                print(f"  ⚠️  Failed to add {user} to {group}: {result.stderr.strip()}")
        else:
            print(f"  ✅ {user} already in {group} group")


def _setup_udev_rule():
    """Create udev rule for /dev/uinput group access"""
    rule_path = Path("/etc/udev/rules.d/99-uinput.rules")

    try:
        if rule_path.exists() and rule_path.read_text() == UINPUT_UDEV_RULE:
            print("  ✅ udev rule already in place")
            return
    except PermissionError:
        pass

    result = _run_sudo(["tee", str(rule_path)], input_text=UINPUT_UDEV_RULE)
    if result.returncode == 0:
        _run_sudo(["udevadm", "control", "--reload-rules"])
        _run_sudo(["udevadm", "trigger"])
        print("  ✅ udev rule created and reloaded")
    else:
        print(f"  ⚠️  Failed to write udev rule: {result.stderr.strip()}")


def _setup_tmpfiles(dotfiles_dir):
    """Deploy tmpfiles.d rule to set /dev/uinput permissions on boot"""
    source = dotfiles_dir / "linuxcommon" / "tmpfiles.d" / "uinput.conf"
    if not source.exists():
        print(f"  ⚠️  uinput.conf not found at {source}")
        return

    dest = Path("/etc/tmpfiles.d/uinput.conf")
    content = source.read_text()

    try:
        if dest.exists() and dest.read_text() == content:
            print("  ✅ tmpfiles.d uinput rule already in place")
            return
    except PermissionError:
        pass

    result = _run_sudo(["tee", str(dest)], input_text=content)
    if result.returncode == 0:
        _run_sudo(["systemd-tmpfiles", "--create", str(dest)])
        print("  ✅ tmpfiles.d uinput rule deployed and applied")
    else:
        print(f"  ⚠️  Failed to write tmpfiles.d rule: {result.stderr.strip()}")


def _setup_system_service(dotfiles_dir):
    """Install and enable the kanata system service"""
    source = dotfiles_dir / "linuxcommon" / "systemd" / "system" / "kanata.service"
    if not source.exists():
        print(f"  ⚠️  kanata.service source not found at {source}")
        return

    service_content = source.read_text()
    service_path = Path("/etc/systemd/system/kanata.service")

    try:
        if service_path.exists() and service_path.read_text() == service_content:
            print("  ✅ kanata.service already up to date")
            _ensure_enabled()
            return
    except PermissionError:
        pass

    result = _run_sudo(["tee", str(service_path)], input_text=service_content)
    if result.returncode != 0:
        print(f"  ⚠️  Failed to write kanata.service: {result.stderr.strip()}")
        return

    _run_sudo(["systemctl", "daemon-reload"])
    print("  ✅ kanata.service installed")
    _ensure_enabled()


def _ensure_enabled():
    check = subprocess.run(
        ["systemctl", "is-enabled", "kanata.service"],
        capture_output=True, text=True
    )
    if check.stdout.strip() != "enabled":
        result = _run_sudo(["systemctl", "enable", "kanata.service"])
        if result.returncode == 0:
            print("  ✅ kanata.service enabled")
        else:
            print(f"  ⚠️  Failed to enable kanata.service: {result.stderr.strip()}")
    else:
        print("  ✅ kanata.service already enabled")


def _install_kanata_tools(dotfiles_dir):
    """Install kanata-tools via uv tool install"""
    if not Path("/home/rash/.local/bin/uv").exists() and \
       subprocess.run(["which", "uv"], capture_output=True).returncode != 0:
        print("  ⚠️  uv not found, skipping kanata-tools install")
        return

    # Check if already installed
    check = subprocess.run(
        ["uv", "tool", "list"],
        capture_output=True, text=True
    )
    if "kanata-tools" in check.stdout:
        print("  ✅ kanata-tools already installed")
        return

    tools_path = dotfiles_dir / "linuxcommon" / "python-tools" / "kanata-tools"
    if not tools_path.exists():
        print("  ⚠️  kanata-tools source not found in linuxcommon/python-tools/")
        return

    result = subprocess.run(
        ["uv", "tool", "install", str(tools_path)],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print("  ✅ kanata-tools installed")
    else:
        print(f"  ⚠️  Failed to install kanata-tools: {result.stderr.strip()}")
