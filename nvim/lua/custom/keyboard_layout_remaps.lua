-- Neovim-specific Colemak for insert mode only
-- Kanata handles Colemak globally, but Neovim can selectively ignore it
-- Reads layout from /tmp/active_keyboard_layout

-- Colemak key mappings (QWERTY -> Colemak)
local colemak_mappings = {
	{'e', 'f'}, {'E', 'F'}, {'r', 'p'}, {'R', 'P'}, {'t', 'g'}, {'T', 'G'},
	{'y', 'j'}, {'Y', 'J'}, {'u', 'l'}, {'U', 'L'}, {'i', 'u'}, {'I', 'U'},
	{'o', 'y'}, {'O', 'Y'}, {'p', 'ö'}, {'P', 'Ö'}, {'s', 'r'}, {'S', 'R'},
	{'d', 's'}, {'D', 'S'}, {'f', 't'}, {'F', 'T'}, {'g', 'd'}, {'G', 'D'},
	{'j', 'n'}, {'J', 'N'}, {'k', 'e'}, {'K', 'E'}, {'l', 'i'}, {'L', 'I'},
	{'ö', 'o'}, {'Ö', 'O'}, {'n', 'k'}, {'N', 'K'}
}

-- Apply Colemak keymaps
local function apply_colemak_keymaps()
	for _, mapping in ipairs(colemak_mappings) do
		vim.keymap.set('i', mapping[1], mapping[2], { noremap = true, silent = true, buffer = true })
	end
	print("Colemak active")
end

-- Remove Colemak keymaps
local function remove_colemak_keymaps()
	for _, mapping in ipairs(colemak_mappings) do
		pcall(vim.keymap.del, 'i', mapping[1], { buffer = true })
	end
	print("QWERTY active")
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
	

	if layout == "cmk" then
		-- When Kanata is in Colemak mode, Neovim applies Colemak ONLY to insert mode
		-- Normal mode keeps QWERTY movement keys (hjkl) for navigation
		-- This creates the perfect hybrid: Colemak for typing, QWERTY for vim navigation

		-- Clear langmap to avoid affecting normal mode
		vim.opt.langmap = ""

		-- Store that we want Colemak mode
		vim.g.colemak_mode = true

		print("Neovim: Colemak insert mode + QWERTY navigation")
	elseif layout == "swe" then
		-- Swedish QWERTY - clear everything
		vim.opt.langmap = ""
		
		-- Store that we want Swedish mode
		vim.g.colemak_mode = false

		print("Neovim: Swedish QWERTY layout active")
	else
		print("Unknown layout: " .. layout .. ". Using Swedish QWERTY.")
		vim.opt.langmap = ""
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
					local old_layout = vim.g.detected_keyboard_layout
					local old_colemak_mode = vim.g.colemak_mode
					setup_keyboard_layout()
					local new_layout = vim.g.detected_keyboard_layout
					local new_colemak_mode = vim.g.colemak_mode

					if old_layout ~= new_layout then
						if new_layout == "cmk" then
							print("Switched to Colemak hybrid layout")
						elseif new_layout == "swe" then
							print("Switched to Swedish QWERTY layout")
						else
							print("Switched to " .. new_layout .. " layout")
						end
						
						-- If we're currently in insert mode, apply/remove keymaps immediately
						local current_mode = vim.api.nvim_get_mode().mode
						if current_mode == "i" or current_mode == "R" then
							if old_colemak_mode and not new_colemak_mode then
								-- Switching from Colemak to Swedish while in insert mode
								remove_colemak_keymaps()
							elseif not old_colemak_mode and new_colemak_mode then
								-- Switching from Swedish to Colemak while in insert mode
								apply_colemak_keymaps()
							end
						end
					else
						print("Layout reloaded: " .. new_layout)
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


-- Autocmds to apply/remove Colemak keymaps on insert mode enter/leave
local colemak_group = vim.api.nvim_create_augroup("ColemakModeHandler", { clear = true })

vim.api.nvim_create_autocmd("InsertEnter", {
	group = colemak_group,
	callback = function()
		if vim.g.colemak_mode then
			apply_colemak_keymaps()
		end
	end,
})

vim.api.nvim_create_autocmd("InsertLeave", {
	group = colemak_group,
	callback = function()
		if vim.g.colemak_mode then
			remove_colemak_keymaps()
		end
	end,
})

-- Test command
vim.api.nvim_create_user_command("TestColemakLayout", function()
	local layout = vim.g.detected_keyboard_layout or "unknown"
	print("Current layout: " .. layout)
	print("Colemak mode: " .. tostring(vim.g.colemak_mode))

	if layout == "cmk" then
		print("✓ HYBRID COLEMAK ACTIVE")
		print("Movement: hjkl (QWERTY navigation)")
		print("Insert mode: Colemak layout (e->f, r->p, etc.)")
		print("Keybinds: <leader>sf, <C-j> work as normal (QWERTY)")
		print("Hyprland: Uses QWERTY for Super+key combinations")
	elseif layout == "swe" then
		print("✓ SWEDISH QWERTY ACTIVE")
		print("Everything uses standard QWERTY positions")
	end
end, { desc = "Test current Colemak setup" })
