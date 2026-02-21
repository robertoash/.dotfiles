"""
Claude Code configuration setup with sops-encrypted secrets.

Reads declarative tools.yaml manifests to configure MCP servers,
substituting sops-encrypted secrets and optionally running install hooks.
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


def setup_claude_config(dotfiles_dir, hostname=None):
    """Setup Claude Code MCP servers with encrypted secrets."""
    dotfiles_dir = Path(dotfiles_dir)

    if hostname is None:
        import socket
        hostname = socket.gethostname()

    # Paths
    common_secrets_file = dotfiles_dir / "common" / "secrets" / "common.yaml"
    machine_secrets_file = dotfiles_dir / hostname / "secrets" / f"{hostname}.yaml"
    common_tools_file = dotfiles_dir / "common" / ".claude" / "tools.yaml"
    machine_tools_file = dotfiles_dir / hostname / ".claude" / "tools.yaml"
    claude_json_path = Path.home() / ".claude.json"

    print("\n🔐 Setting up Claude Code configuration...")

    tool_permissions = []
    mcp_setup_success = False

    try:
        env = os.environ.copy()
        age_key_file = Path.home() / ".config" / "sops" / "age" / "keys.txt"
        if age_key_file.exists():
            env["SOPS_AGE_KEY_FILE"] = str(age_key_file)

        subprocess.run(["sops", "--version"], capture_output=True, check=True, env=env)

        if common_secrets_file.exists():
            secrets = decrypt_secrets(common_secrets_file)
            if machine_secrets_file.exists():
                machine_secrets = decrypt_secrets(machine_secrets_file)
                if machine_secrets:
                    secrets.update(machine_secrets)
                    print(f"  🔑 Merged secrets from {hostname}/secrets/{hostname}.yaml")

            if secrets:
                # Load and merge tool manifests (machine overrides common)
                tools = load_tools_yaml(common_tools_file)
                machine_tools = load_tools_yaml(machine_tools_file)
                tools.update(machine_tools)

                # Filter out disabled tools
                tools = {name: cfg for name, cfg in tools.items() if cfg.get("enabled", True)}

                # Run install hooks
                for name, cfg in tools.items():
                    run_install_hook(name, cfg)

                # Build MCP servers dict with secret substitution
                mcp_servers = {}
                for name, cfg in tools.items():
                    perms = cfg.get("permissions")
                    if perms:
                        tool_permissions.append(perms)

                    server = {}
                    for key in _MCP_KEYS:
                        if key in cfg:
                            server[key] = substitute_secrets(cfg[key], secrets)
                    mcp_servers[name] = server

                # Sync to ~/.claude.json
                if claude_json_path.exists():
                    with open(claude_json_path) as f:
                        claude_config = json.load(f)
                else:
                    claude_config = {}

                if "mcpServers" not in claude_config:
                    claude_config["mcpServers"] = {}

                for server in [s for s in claude_config["mcpServers"] if s not in mcp_servers]:
                    del claude_config["mcpServers"][server]
                    print(f"  🗑️  Removed obsolete MCP server: {server}")

                claude_config["mcpServers"].update(mcp_servers)

                with open(claude_json_path, "w") as f:
                    json.dump(claude_config, f, indent=2)

                print(f"✅ Updated {claude_json_path} with {len(mcp_servers)} MCP server(s)")
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

    # Merge settings.json from dotfiles into ~/.claude/settings.json
    settings_source = dotfiles_dir / "common" / ".claude" / "settings.json"
    settings_target = Path.home() / ".claude" / "settings.json"

    if settings_source.exists():
        settings_target.parent.mkdir(parents=True, exist_ok=True)

        with open(settings_source) as f:
            source_settings = json.load(f)

        if settings_target.exists():
            with open(settings_target) as f:
                target_settings = json.load(f)
        else:
            target_settings = {}

        for key, value in source_settings.items():
            if key == "permissions":
                if "permissions" not in target_settings:
                    target_settings["permissions"] = {}
                for perm_type in ["allow", "deny", "ask"]:
                    if perm_type in value:
                        target_settings["permissions"][perm_type] = value[perm_type]
            else:
                target_settings[key] = value

        # Append tool-specific permissions from tools.yaml
        if mcp_setup_success and tool_permissions:
            if "permissions" not in target_settings:
                target_settings["permissions"] = {}
            for perms in tool_permissions:
                for perm_type in ["allow", "deny", "ask"]:
                    if perm_type in perms:
                        existing = target_settings["permissions"].get(perm_type, [])
                        for entry in perms[perm_type]:
                            if entry not in existing:
                                existing.append(entry)
                        target_settings["permissions"][perm_type] = existing

        with open(settings_target, "w") as f:
            json.dump(target_settings, f, indent=2)

        print(f"✅ Updated {settings_target} with dotfiles settings")
    else:
        print(f"⚠️  settings.json not found at {settings_source}")

    common = dotfiles_dir / "common" / ".claude"
    claude = Path.home() / ".claude"
    for name in ("CLAUDE.md", "scripts", "commands"):
        _symlink_claude_item(common / name, claude / name)

    return True
