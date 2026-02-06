#!/usr/bin/env python3
"""
Zen app window rules generator.
Reads linuxmini/config/hypr/script_configs/zen_apps.json and generates:
- {machine}/config/hypr/zen_app_windowrules.conf (Hyprland window rules)
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, List, Tuple
from urllib.parse import urlparse


def load_zen_apps_config(dotfiles_dir: Path, machine: str) -> Dict[str, Any]:
    """Load zen apps configuration from JSON"""
    config_file = dotfiles_dir / machine / "config" / "hypr" / "script_configs" / "zen_apps.json"

    if not config_file.exists():
        raise FileNotFoundError(f"Zen apps config not found: {config_file}")

    with open(config_file) as f:
        return json.load(f)


def extract_extension_id(extension_url: str) -> str:
    """Extract extension ID from chrome-extension:// URL"""
    match = re.match(r'chrome-extension://([a-z]+)/.*', extension_url)
    if match:
        return match.group(1)
    raise ValueError(f"Invalid extension URL: {extension_url}")


def extract_domain(url: str) -> str:
    """Extract domain from URL for matching"""
    parsed = urlparse(url)
    domain = parsed.netloc
    # Remove www. prefix if present
    if domain.startswith('www.'):
        domain = domain[4:]
    return domain


def generate_window_rule_line(rule_type: str, rule_value: Any, match_pattern: str) -> str:
    """Generate a single windowrule line"""
    # Rules that should keep underscores (don't convert to spaces)
    keep_underscores = ["keep_aspect_ratio"]

    # Handle boolean rules (float, pin, keep_aspect_ratio)
    if isinstance(rule_value, bool):
        value_str = "on" if rule_value else "off"
        # Keep underscores for certain rules, otherwise convert to spaces
        rule_name = rule_type if rule_type in keep_underscores else rule_type.replace("_", " ")
        return f"windowrule = {rule_name} {value_str}, {match_pattern}"
    else:
        # Handle string rules (size, move, etc.)
        rule_name = rule_type if rule_type in keep_underscores else rule_type.replace("_", " ")
        return f"windowrule = {rule_name} {rule_value}, {match_pattern}"


def generate_windowrules_for_app(
    app_name: str,
    app_type: str,
    app_data: Dict[str, Any]
) -> List[str]:
    """Generate windowrule lines for a single app"""
    if "window_rules" not in app_data:
        return []

    lines = []
    window_rules = app_data["window_rules"]
    app_url = app_data["app_url"]

    # Determine match pattern based on app type
    if app_type == "extension":
        extension_id = extract_extension_id(app_url)
        # Extension windows use initial_title with format: {extension-id}_/popup/index.html
        match_pattern = f"match:initial_title ^{extension_id}_/popup/index.html$"
    else:  # url type
        domain = extract_domain(app_url)
        # URL apps use initial_title with domain pattern
        match_pattern = f"match:initial_title ^{domain}.*$"

    # Add comment for the app
    lines.append(f"# {app_name} ({app_type})")

    # Generate rules in a consistent order
    rule_order = ["workspace", "float", "pin", "size", "move", "keep_aspect_ratio"]
    for rule_type in rule_order:
        if rule_type in window_rules:
            rule_line = generate_window_rule_line(
                rule_type,
                window_rules[rule_type],
                match_pattern
            )
            lines.append(rule_line)

    return lines


def generate_zen_app_windowrules_file(config: Dict[str, Any]) -> str:
    """
    Generate zen_app_windowrules.conf content from zen_apps.json.
    Returns the file content as a string.
    """
    lines = [
        "# AUTO-GENERATED FROM zen_apps.json",
        "# DO NOT EDIT - Run setup.py to regenerate",
        "",
    ]

    # Process both URL and extension apps
    for app_type in ["url", "extension"]:
        if app_type not in config:
            continue

        for app_name, app_data in config[app_type].items():
            app_rules = generate_windowrules_for_app(app_name, app_type, app_data)
            if app_rules:
                lines.extend(app_rules)
                lines.append("")  # Empty line between apps

    # Remove trailing empty line if present
    if lines and lines[-1] == "":
        lines = lines[:-1]

    return "\n".join(lines)


def generate_zen_app_windowrules(dotfiles_dir: Path, machine: str, verbose: bool = True) -> None:
    """
    Main generation function.
    Reads zen_apps.json and generates zen_app_windowrules.conf.
    """
    if verbose:
        print("\n🪟 Generating Hyprland window rules from zen_apps.json...")

    # Load configuration
    config = load_zen_apps_config(dotfiles_dir, machine)

    # Generate windowrules file
    output_file = dotfiles_dir / machine / "config" / "hypr" / "zen_app_windowrules.conf"
    content = generate_zen_app_windowrules_file(config)
    output_file.write_text(content)

    if verbose:
        print(f"  ✅ Generated {output_file}")
        print("  ✨ Zen app window rules generation complete!")


if __name__ == "__main__":
    # Allow running this script standalone for testing
    import socket
    dotfiles_dir = Path(__file__).parent.parent
    machine = socket.gethostname()
    generate_zen_app_windowrules(dotfiles_dir, machine, verbose=True)
    print("  💡 Reload Hyprland: hyprctl reload")
