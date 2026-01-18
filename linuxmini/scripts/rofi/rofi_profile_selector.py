#!/usr/bin/env python3

"""
Modular profile selector for applications using rofi
Supports multiple applications with configurable profiles
Enhanced to handle meeting URLs from calendar notifications
"""

import os
import subprocess
import sys
from typing import Dict, List, Union


class ProfileSelector:
    """A modular profile selector that uses rofi for selection and executes
    application commands directly."""

    def __init__(self):
        """Initialize the profile selector with application configurations."""
        # Load chromium profiles from hypr_window_ops config
        chromium_profiles = self._load_chromium_profiles()
        
        self.applications = {
            "qutebrowser": {
                "profiles": ["rash", "company"],
                "command_template": "/home/rash/.local/bin/qute_profile {profile}",
            },
            "chromium": {
                "profiles": chromium_profiles,
                "command_template": (
                    "/home/rash/.local/bin/chromium_launch --profile {profile}"
                ),
            },
        }

    def _load_chromium_profiles(self):
        """Load chromium profiles from hypr_window_ops config."""
        try:
            import sys
            from pathlib import Path
            
            # Add the config module path to sys.path temporarily
            config_dir = Path.home() / ".config/scripts/hyprland/hypr_window_ops"
            sys.path.insert(0, str(config_dir))
            
            from hypr_window_ops import config
            
            return list(config.BROWSER_PROFILES.keys())
        except Exception as e:
            print(f"Warning: Could not load chromium profiles from config, using defaults: {e}")
            return ["rash", "company", "app", "dash"]

    def _is_template_based(self, app_name: str) -> bool:
        """Check if application uses template-based configuration."""
        if app_name not in self.applications:
            raise ValueError(f"Application '{app_name}' not configured")
        return "command_template" in self.applications[app_name]

    def get_application_profiles(self, app_name: str) -> List[str]:
        """Get the list of profiles for a given application."""
        if app_name not in self.applications:
            raise ValueError(f"Application '{app_name}' not configured")

        config = self.applications[app_name]
        if self._is_template_based(app_name):
            return config["profiles"]
        else:
            # Dictionary-based format: profiles is a dict
            return list(config["profiles"].keys())

    def get_command(self, app_name: str, profile: str, url: str = None) -> str:
        """Generate the command for a given application and profile."""
        if app_name not in self.applications:
            raise ValueError(f"Application '{app_name}' not configured")

        config = self.applications[app_name]

        if self._is_template_based(app_name):
            # Template-based format
            command = config["command_template"].format(profile=profile)
        else:
            # Dictionary-based format
            if profile not in config["profiles"]:
                raise ValueError(
                    f"Profile '{profile}' not found for application '{app_name}'"
                )
            command = config["profiles"][profile]

        # Add URL if provided
        if url:
            command += f" '{url}'"

        # Expand tilde in the command
        return os.path.expanduser(command)

    def show_profile_menu(self, app_name: str) -> str:
        """Show rofi menu for profile selection and return the selected profile."""
        profiles = self.get_application_profiles(app_name)
        profiles_str = "\n".join(profiles)

        try:
            result = subprocess.run(
                ["rofi", "-dmenu", "-i", "-p", f"Select {app_name} profile:"],
                input=profiles_str,
                text=True,
                capture_output=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            # User cancelled or rofi failed
            return ""

    def show_application_menu(self) -> str:
        """Show rofi menu for application selection and return the selected application."""
        applications = list(self.applications.keys())
        applications_str = "\n".join(applications)

        try:
            result = subprocess.run(
                ["rofi", "-dmenu", "-i", "-p", "Select browser:"],
                input=applications_str,
                text=True,
                capture_output=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            # User cancelled or rofi failed
            return ""

    def launch_profile(self, app_name: str, profile: str, url: str = None) -> bool:
        """Launch the specified profile for the given application."""
        if not profile:
            return False

        try:
            command = self.get_command(app_name, profile, url)

            # Split command into list for subprocess, handling quoted URLs
            if url:
                # If URL is present, split carefully to preserve the URL as one argument
                import shlex

                cmd_list = shlex.split(command)
            else:
                cmd_list = command.split()

            # Launch in background (detached from terminal)
            subprocess.Popen(
                cmd_list,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )

            return True
        except Exception as e:
            print(
                f"Error launching {app_name} profile '{profile}': {e}", file=sys.stderr
            )
            return False

    def run_selector(self, app_name: str, url: str = None) -> None:
        """Run the complete profile selection process for an application."""
        if app_name not in self.applications:
            print(f"Error: Application '{app_name}' not configured", file=sys.stderr)
            sys.exit(1)

        selected_profile = self.show_profile_menu(app_name)
        if selected_profile:
            success = self.launch_profile(app_name, selected_profile, url)
            if not success:
                sys.exit(1)

    def add_application_template(
        self,
        app_name: str,
        profiles: List[str],
        command_template: str,
    ) -> None:
        """Add a new application configuration using template format."""
        self.applications[app_name] = {
            "profiles": profiles,
            "command_template": command_template,
        }

    def add_application_dict(
        self,
        app_name: str,
        profiles: Dict[str, str],
    ) -> None:
        """Add a new application configuration using dictionary format."""
        self.applications[app_name] = {
            "profiles": profiles,
        }

    def add_application(
        self,
        app_name: str,
        profiles: Union[List[str], Dict[str, str]],
        command_template: str = None,
    ) -> None:
        """Add a new application configuration (backward compatibility)."""
        if isinstance(profiles, dict):
            self.add_application_dict(app_name, profiles)
        elif command_template:
            self.add_application_template(app_name, profiles, command_template)
        else:
            raise ValueError(
                "Either profiles must be a dict or command_template must be provided"
            )


def main():
    """Main entry point."""
    selector = ProfileSelector()

    # Check for URL from command line or environment variable
    url = None
    app_name = None

    if len(sys.argv) >= 2:
        first_arg = sys.argv[1]
        # Check if first argument is a URL (called from desktop entry)
        if first_arg.startswith(('http://', 'https://', 'about:', 'file://')):
            url = first_arg
            # Show browser selection since no app specified
            app_name = selector.show_application_menu()
            if not app_name:
                sys.exit(0)
        else:
            # First argument is the application name
            app_name = first_arg.lower()
            if len(sys.argv) > 2:
                url = sys.argv[2]

    if not app_name:
        # No application specified, show browser selection menu
        app_name = selector.show_application_menu()
        if not app_name:
            # User cancelled
            sys.exit(0)

    # Check for MEETING_URL environment variable if no URL from command line
    if not url and "MEETING_URL" in os.environ:
        url = os.environ["MEETING_URL"]

    selector.run_selector(app_name, url)


if __name__ == "__main__":
    main()
