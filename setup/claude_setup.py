"""
Claude Code configuration setup with sops-encrypted secrets.

Reads declarative tools.yaml manifests to configure MCP servers,
substituting sops-encrypted secrets and optionally running install hooks.

Profiles
--------
Each tool in tools.yaml can declare which profiles it belongs to:

    hass-mcp:
      profiles: [work, personal]   # omit = all profiles
      command: docker
      ...

Profile-specific settings overlays live alongside settings.json:

    common/.claude/settings.json           # base, all profiles
    common/.claude/settings.personal.json  # merged on top for personal

setup.py generates per-profile MCP caches at:
    ~/.config/claude-profiles/{profile}.json

The `cc` fish function uses these caches to swap MCPs in ~/.claude.json
and set CLAUDE_CONFIG_DIR when switching profiles.
"""

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import yaml


def decrypt_secrets(secrets_file):
    """Decrypt sops secrets file and return as dict."""
    try:
        env = os.environ.copy()
        age_key_file = Path.home() / ".config" / "sops" / "age" / "keys.txt"
        if age_key_file.exists():
            env["SOPS_AGE_KEY_FILE"] = str(age_key_file)

        result = subprocess.run(
            ["sops", "-d", str(secrets_file)],
            capture_output=True,
            text=True,
            check=True,
            env=env,
        )
        return yaml.safe_load(result.stdout) or {}
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Error decrypting secrets: {e.stderr}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"⚠️  Error parsing secrets: {e}", file=sys.stderr)
        return None


def substitute_secrets(value, secrets):
    """Replace {{key}} placeholders with secret values recursively."""
    if isinstance(value, str):
        return re.sub(
            r"\{\{(.+?)\}\}",
            lambda m: str(secrets.get(m.group(1), m.group(0))),
            value,
        )
    if isinstance(value, list):
        return [substitute_secrets(item, secrets) for item in value]
    if isinstance(value, dict):
        return {k: substitute_secrets(v, secrets) for k, v in value.items()}
    return value


def load_tools_yaml(path):
    """Load a tools.yaml manifest, returning {} if missing or empty."""
    if not path.exists():
        return {}
    with open(path) as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else {}


def run_install_hook(tool_name, tool_config):
    """Run a tool's install or update hook based on whether command exists."""
    install_cmd = tool_config.get("install")
    update_cmd = tool_config.get("update")
    command = tool_config.get("command", "")

    if not install_cmd and not update_cmd:
        return

    command_exists = shutil.which(command)

    # If command exists and we have an update hook, run update
    if command_exists and update_cmd:
        print(f"  🔄 Updating {tool_name}: {update_cmd}")
        try:
            subprocess.run(update_cmd, shell=True, check=True, capture_output=True, text=True)
            print(f"  ✅ Updated {tool_name}")
        except subprocess.CalledProcessError as e:
            print(f"  ⚠️  Update hook failed for {tool_name}: {e.stderr}", file=sys.stderr)
        return

    # If command doesn't exist and we have an install hook, run install
    if not command_exists and install_cmd:
        print(f"  📦 Installing {tool_name}: {install_cmd}")
        try:
            subprocess.run(install_cmd, shell=True, check=True, capture_output=True, text=True)
            print(f"  ✅ Installed {tool_name}")
        except subprocess.CalledProcessError as e:
            print(f"  ⚠️  Install hook failed for {tool_name}: {e.stderr}", file=sys.stderr)


# Keys from tools.yaml that map directly to MCP server config
_MCP_KEYS = ("type", "command", "args", "env", "url")


def _symlink_claude_item(source, target):
    if not source.exists():
        print(f"⚠️  Not found: {source}")
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() or target.is_symlink():
        target.unlink() if (target.is_symlink() or target.is_file()) else shutil.rmtree(target)
    target.symlink_to(source.resolve())
    print(f"✅ Symlinked {target} -> {source}")


def _discover_profiles(tools, common_claude_dir):
    """Collect profile names from tool declarations and settings overlay files."""
    profiles = {"work"}
    for cfg in tools.values():
        for p in cfg.get("profiles", []):
            profiles.add(p)
    for f in common_claude_dir.glob("settings.*.json"):
        # settings.personal.json -> "personal"
        profiles.add(f.stem.split(".", 1)[1])
    return profiles


def _get_profile_config_dir(profile):
    """~/.claude/ for work, ~/.claude-{profile}/ for others."""
    if profile == "work":
        return Path.home() / ".claude"
    return Path.home() / f".claude-{profile}"


def _filter_tools_for_profile(tools, profile):
    """Return tools that apply to the given profile (no profiles field = all)."""
    return {
        name: cfg for name, cfg in tools.items()
        if not cfg.get("profiles") or profile in cfg["profiles"]
    }


def _merge_settings(target, source):
    """Merge source settings into target, deep-merging the permissions block."""
    for key, value in source.items():
        if key == "permissions":
            target.setdefault("permissions", {})
            for perm_type in ("allow", "deny", "ask"):
                if perm_type in value:
                    target["permissions"][perm_type] = value[perm_type]
        else:
            target[key] = value


def _append_tool_permissions(target, tool_permissions):
    """Append per-tool permission entries, avoiding duplicates."""
    target.setdefault("permissions", {})
    for perms in tool_permissions:
        for perm_type in ("allow", "deny", "ask"):
            if perm_type in perms:
                existing = target["permissions"].setdefault(perm_type, [])
                for entry in perms[perm_type]:
                    if entry not in existing:
                        existing.append(entry)


def setup_claude_config(dotfiles_dir, hostname=None):
    """Setup Claude Code MCP servers and settings for all profiles."""
    dotfiles_dir = Path(dotfiles_dir)

    if hostname is None:
        import socket
        hostname = socket.gethostname()

    common_secrets_file = dotfiles_dir / "common" / "secrets" / "common.yaml"
    machine_secrets_file = dotfiles_dir / hostname / "secrets" / f"{hostname}.yaml"
    common_tools_file = dotfiles_dir / "common" / ".claude" / "tools.yaml"
    machine_tools_file = dotfiles_dir / hostname / ".claude" / "tools.yaml"
    common_claude_dir = dotfiles_dir / "common" / ".claude"
    claude_json_path = Path.home() / ".claude.json"

    print("\n🔐 Setting up Claude Code configuration...")

    mcp_setup_success = False
    secrets = {}
    tools = {}

    try:
        env = os.environ.copy()
        age_key_file = Path.home() / ".config" / "sops" / "age" / "keys.txt"
        if age_key_file.exists():
            env["SOPS_AGE_KEY_FILE"] = str(age_key_file)

        subprocess.run(["sops", "--version"], capture_output=True, check=True, env=env)

        if common_secrets_file.exists():
            secrets = decrypt_secrets(common_secrets_file) or {}
            if machine_secrets_file.exists():
                machine_secrets = decrypt_secrets(machine_secrets_file)
                if machine_secrets:
                    secrets.update(machine_secrets)
                    print(f"  🔑 Merged secrets from {hostname}/secrets/{hostname}.yaml")

            if secrets:
                tools = load_tools_yaml(common_tools_file)
                machine_tools = load_tools_yaml(machine_tools_file)
                tools.update(machine_tools)
                tools = {name: cfg for name, cfg in tools.items() if cfg.get("enabled", True)}

                for name, cfg in tools.items():
                    run_install_hook(name, cfg)

                mcp_setup_success = True
            else:
                print("⚠️  Failed to decrypt secrets. Skipping MCP servers setup.")
        else:
            print(f"⚠️  Secrets file not found: {common_secrets_file}")
            print("⚠️  Skipping MCP servers setup.")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  sops not found. Skipping MCP servers setup.")
    except Exception as e:
        print(f"⚠️  Error setting up MCP servers: {e}")

    # --- Per-profile configuration ---

    profiles = _discover_profiles(tools, common_claude_dir)
    profiles_cache_dir = Path.home() / ".config" / "claude-profiles"
    profiles_cache_dir.mkdir(parents=True, exist_ok=True)
    base_settings_file = common_claude_dir / "settings.json"

    for profile in sorted(profiles):
        profile_tools = _filter_tools_for_profile(tools, profile)
        config_dir = _get_profile_config_dir(profile)
        config_dir.mkdir(parents=True, exist_ok=True)

        # Build MCP servers for this profile
        mcp_servers = {}
        tool_permissions = []
        if mcp_setup_success:
            for name, cfg in profile_tools.items():
                perms = cfg.get("permissions")
                if perms:
                    tool_permissions.append(perms)
                server = {key: substitute_secrets(cfg[key], secrets) for key in _MCP_KEYS if key in cfg}
                mcp_servers[name] = server

        # Cache profile MCPs for use by the cc fish function
        with open(profiles_cache_dir / f"{profile}.json", "w") as f:
            json.dump({"mcpServers": mcp_servers}, f, indent=2)

        # Build settings: read existing → apply base → apply profile overlay → append tool perms
        settings_path = config_dir / "settings.json"
        target_settings = {}
        if settings_path.exists():
            with open(settings_path) as f:
                target_settings = json.load(f)

        if base_settings_file.exists():
            with open(base_settings_file) as f:
                _merge_settings(target_settings, json.load(f))

        profile_settings_file = common_claude_dir / f"settings.{profile}.json"
        if profile_settings_file.exists():
            with open(profile_settings_file) as f:
                _merge_settings(target_settings, json.load(f))
            print(f"  🎨 Applied settings.{profile}.json overlay")

        if tool_permissions:
            _append_tool_permissions(target_settings, tool_permissions)

        with open(settings_path, "w") as f:
            json.dump(target_settings, f, indent=2)

        print(f"✅ Updated {settings_path} ({profile} profile)")

        # Symlink shared claude items into each profile's config dir
        for name in ("CLAUDE.md", "scripts", "commands"):
            _symlink_claude_item(common_claude_dir / name, config_dir / name)

    # Update ~/.claude.json with the work profile's MCP servers.
    # The cc fish function swaps this when switching profiles.
    if mcp_setup_success:
        work_cache = profiles_cache_dir / "work.json"
        with open(work_cache) as f:
            work_mcp_servers = json.load(f)["mcpServers"]

        if claude_json_path.exists():
            with open(claude_json_path) as f:
                claude_config = json.load(f)
        else:
            claude_config = {}

        claude_config.setdefault("mcpServers", {})

        for server in [s for s in claude_config["mcpServers"] if s not in work_mcp_servers]:
            del claude_config["mcpServers"][server]
            print(f"  🗑️  Removed obsolete MCP server: {server}")

        claude_config["mcpServers"].update(work_mcp_servers)

        with open(claude_json_path, "w") as f:
            json.dump(claude_config, f, indent=2)

        print(f"✅ Updated {claude_json_path} with {len(work_mcp_servers)} work MCP server(s)")

    return True
