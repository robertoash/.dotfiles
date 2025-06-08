#!/usr/bin/env python3

"""
Modular profile selector for applications using rofi
Supports multiple applications with configurable profiles
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
        self.applications = {
            "qutebrowser": {
                "profiles": ["rash", "jobhunt"],
                "command_template": "/home/rash/.local/bin/qute_profile {profile}",
            },
            "vivaldi": {
                "profiles": ["rash", "jobhunt", "app_profile"],
                "command_template": (
                    "/home/rash/.local/bin/vivaldi_launch --profile {profile}"
                ),
            },
            # Example of dictionary-based app (each profile has its own command)
            # "example_app": {
            #    "profiles": {
            #        "dev": "example_app --env dev --debug",
            #        "prod": "example_app --env production",
            #        "local": "/path/to/local_version --config local.conf",
            #    }
            # },
        }

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

    def get_command(self, app_name: str, profile: str) -> str:
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

    def launch_profile(self, app_name: str, profile: str) -> bool:
        """Launch the specified profile for the given application."""
        if not profile:
            return False

        try:
            command = self.get_command(app_name, profile)
            # Split command into list for subprocess
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

    def run_selector(self, app_name: str) -> None:
        """Run the complete profile selection process for an application."""
        if app_name not in self.applications:
            print(f"Error: Application '{app_name}' not configured", file=sys.stderr)
            sys.exit(1)

        selected_profile = self.show_profile_menu(app_name)
        if selected_profile:
            success = self.launch_profile(app_name, selected_profile)
            if not success:
                sys.exit(1)

    def add_application_template(
        self,
        app_name: str,
        profiles: List[str],
        command_template: str,
    ) -> None:
        """Add a new application configuration using template format.

        Args:
            app_name: Name of the application
            profiles: List of available profiles
            command_template: Command template with {profile} placeholder
        """
        self.applications[app_name] = {
            "profiles": profiles,
            "command_template": command_template,
        }

    def add_application_dict(
        self,
        app_name: str,
        profiles: Dict[str, str],
    ) -> None:
        """Add a new application configuration using dictionary format.

        Args:
            app_name: Name of the application
            profiles: Dictionary mapping profile names to commands
        """
        self.applications[app_name] = {
            "profiles": profiles,
        }

    # Backward compatibility method
    def add_application(
        self,
        app_name: str,
        profiles: Union[List[str], Dict[str, str]],
        command_template: str = None,
    ) -> None:
        """Add a new application configuration (backward compatibility).

        Args:
            app_name: Name of the application
            profiles: List of profiles (template mode) or dict of profile->command (dict mode)
            command_template: Command template (only used in template mode)
        """
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
    if len(sys.argv) != 2:
        print("Usage: rofi_profile_selector.py <application_name>", file=sys.stderr)
        print("Available applications: qutebrowser, vivaldi", file=sys.stderr)
        sys.exit(1)

    app_name = sys.argv[1].lower()
    selector = ProfileSelector()
    selector.run_selector(app_name)


if __name__ == "__main__":
    main()
