#!/bin/bash
# ~/.config/theme_it/gtk-override.sh

gsettings set org.gnome.desktop.interface gtk-theme "tokyonight_deep"
gsettings set org.gnome.desktop.interface icon-theme "Tokyonight-Moon"
gsettings set org.gnome.desktop.interface font-name "GeistMono Nerd Font 13"
gsettings set org.gnome.desktop.interface monospace-font-name "GeistMono Nerd Font 13"
gsettings set org.gnome.desktop.interface document-font-name "GeistMono Nerd Font 13"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] [theme_it] Applied GTK overrides" >> /tmp/gtk_override.log
