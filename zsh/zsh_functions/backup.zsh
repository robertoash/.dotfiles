# Update all packages from all package managers
update_packages() {
  echo "Updating pacman..."
  sudo pacman -Syu --noconfirm

  echo "Updating yay (AUR)..."
  yay -Syu --devel --noconfirm

  echo "Updating pipx packages..."
  pipx upgrade-all

  echo "Updating flatpak packages..."
  flatpak update -y
}