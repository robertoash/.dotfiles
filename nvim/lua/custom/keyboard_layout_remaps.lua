-- Neovim-specific Colemak for insert mode only
-- Kanata handles Colemak globally, but Neovim can selectively ignore it
-- Reads layout from /tmp/active_keyboard_layout

-- Colemak to QWERTY mappings (Colemak -> QWERTY)
-- Since kanata now outputs colemak keys, we need to remap them back to qwerty for navigation
local colemak_to_qwerty_mappings = {
	{'f', 'e'}, {'F', 'E'}, {'p', 'r'}, {'P', 'R'}, {'g', 't'}, {'G', 'T'},
	{'j', 'y'}, {'J', 'Y'}, {'l', 'u'}, {'L', 'U'}, {'u', 'i'}, {'U', 'I'},
	{'y', 'o'}, {'Y', 'O'}, {'ö', 'p'}, {'Ö', 'P'}, {'r', 's'}, {'R', 'S'},
	{'s', 'd'}, {'S', 'D'}, {'t', 'f'}, {'T', 'F'}, {'d', 'g'}, {'D', 'G'},
	{'n', 'j'}, {'N', 'J'}, {'e', 'k'}, {'E', 'K'}, {'i', 'l'}, {'I', 'L'},
	{'o', 'ö'}, {'O', 'Ö'}, {'k', 'n'}, {'K', 'N'}
}

-- Apply navigation keymaps (colemak -> qwerty for hjkl movement)
local function apply_navigation_keymaps()
	for _, mapping in ipairs(colemak_to_qwerty_mappings) do
		vim.keymap.set('n', mapping[1], mapping[2], { noremap = true, silent = true })
	end
	print("Colemak navigation remapped to QWERTY")
end

-- Remove navigation keymaps
local function remove_navigation_keymaps()
	for _, mapping in ipairs(colemak_to_qwerty_mappings) do
		pcall(vim.keymap.del, 'n', mapping[1])
	end
end

local function setup_keyboard_layout()
	local layout = "swe" -- Default fallback

	-- Read layout from file
	local file = io.open("/tmp/active_keyboard_layout", "r")
	if file then
		local content = file:read("*a")
		file:close()
		if content then
			layout = content:gsub("%s+", "") -- Remove whitespace
		end
	end
	
	-- Normalize layer names - treat plain variants as equivalent to their base layers
	if layout == "colemak_plain" then
		layout = "cmk"
	elseif layout == "nordic_plain" then
		layout = "swe"
	end

	if layout == "cmk" then
		-- When Kanata is in Colemak mode, remap navigation keys to QWERTY positions
		-- This allows hjkl movement to work correctly when kanata outputs colemak keys
		
		-- Remove any existing navigation keymaps first
		remove_navigation_keymaps()
		
		-- Apply colemak->qwerty navigation keymaps
		apply_navigation_keymaps()

		-- Store that we want Colemak mode
		vim.g.colemak_mode = true

		print("Neovim: Colemak with QWERTY navigation remapped")
	elseif layout == "swe" then
		-- Swedish QWERTY - remove any colemak navigation remaps
		remove_navigation_keymaps()
		
		-- Store that we want Swedish mode
		vim.g.colemak_mode = false

	else
		print("Unknown layout: " .. layout .. ". Using Swedish QWERTY.")
		remove_navigation_keymaps()
		vim.g.colemak_mode = false
	end

	vim.g.detected_keyboard_layout = layout
end

-- Initialize on startup
setup_keyboard_layout()

-- Set up file watcher for automatic reloading
local layout_file = "/tmp/active_keyboard_layout"
local watcher = nil

local function start_file_watcher()
	if watcher then
		watcher:stop()
	end

	watcher = vim.loop.new_fs_event()
	if watcher then
		watcher:start(
			layout_file,
			{},
			vim.schedule_wrap(function(err, filename, events)
				if err then
					print("Keyboard layout file watcher error: " .. err)
					return
				end

				if events.change then
					local old_colemak_mode = vim.g.colemak_mode
					setup_keyboard_layout()
					local new_colemak_mode = vim.g.colemak_mode

					-- Only print if the functional mode actually changed
					if old_colemak_mode ~= new_colemak_mode then
						if new_colemak_mode then
							print("Switched to Colemak with QWERTY navigation")
						else
							print("Switched to Swedish QWERTY layout")
						end
					end
				end
			end)
		)
	end
end

-- Start watching
local file = io.open(layout_file, "r")
if file then
	file:close()
	start_file_watcher()
else
	file = io.open(layout_file, "w")
	if file then
		file:write("swe")
		file:close()
		start_file_watcher()
	end
end

-- Clean up watcher on exit
vim.api.nvim_create_autocmd("VimLeavePre", {
	callback = function()
		if watcher then
			watcher:stop()
		end
	end,
})

-- Manual reload command
vim.api.nvim_create_user_command("ReloadKeyboardLayout", function()
	setup_keyboard_layout()
end, { desc = "Reload keyboard layout from /tmp/active_keyboard_layout" })


-- No need for insert mode autocmds since we're now handling navigation keys in normal mode only

-- Test command
vim.api.nvim_create_user_command("TestColemakLayout", function()
	local layout = vim.g.detected_keyboard_layout or "unknown"
	print("Current layout: " .. layout)
	print("Colemak mode: " .. tostring(vim.g.colemak_mode))

	if layout == "cmk" then
		print("✓ COLEMAK WITH QWERTY NAVIGATION ACTIVE")
		print("Kanata outputs: Colemak keys")
		print("Neovim navigation: hjkl remapped to work with colemak (h->h, n->j, e->k, i->l)")
		print("Keybinds: All vim bindings work correctly")
		print("Hyprland: Uses passthrough layer for Super+key combinations")
	elseif layout == "swe" then
		print("✓ SWEDISH QWERTY ACTIVE")
		print("Everything uses standard QWERTY positions")
	end
end, { desc = "Test current Colemak setup" })
