#!/usr/bin/env python3

import subprocess
import sys

SEPARATOR = "///"

def save_packages(filename):
    with open(filename, 'w') as f:  # Open file in write mode
        # Save Pacman packages
        pacman_packages = subprocess.check_output(['pacman', '-Qqe']).decode().splitlines()
        for package in pacman_packages:
            f.write(f"{package}{SEPARATOR}pacman\n")

        # Save Yay packages
        yay_packages = subprocess.check_output(['yay', '-Qqe']).decode().splitlines()
        for package in yay_packages:
            f.write(f"{package}{SEPARATOR}yay\n")

        # Save Pipx packages
        pipx_packages = subprocess.check_output(['pipx', 'list', '--short']).decode().splitlines()
        for package in pipx_packages:
            f.write(f"{package}{SEPARATOR}pipx\n")

def reinstall_packages(filename):
    with open(filename) as f:
        for line in f:
            package, manager = line.strip().split(SEPARATOR)
            if manager == 'pacman':
                subprocess.run(['sudo', 'pacman', '-S', '--noconfirm', package])
            elif manager == 'yay':
                subprocess.run(['yay', '-S', '--noconfirm', package])
            elif manager == 'pipx':
                subprocess.run(['pipx', 'install', package])

if __name__ == "__main__":
    if len(sys.argv) == 3:
        action = sys.argv[1]
        filename = sys.argv[2]
    else:
        print("Usage:")
        print("./package_requirements.py -s <filename> (to save packages)")
        print("./package_requirements.py -r <filename> (to reinstall packages)")
        sys.exit(1)

    if action == '-s':
        save_packages(filename)
        print(f"Packages saved to {filename}")
    elif action == '-r':
        reinstall_packages(filename)
        print(f"Packages reinstalled from {filename}")
    else:
        print("Invalid choice. Exiting.")
