# ~/.config/fish/conf.d/06_startup.fish
# Startup Configuration

# Modify the startup call to use the full path for buku database
switch_buku_db "rash" --startup

# #################################
# # Smart CWD Startup for Starship
# #################################

function update_smart_cwd --on-variable PWD
    set -gx SMART_CWD (python /home/rash/.config/scripts/starship/smart_path.py)
end

# Initialize for the first prompt after login
update_smart_cwd
