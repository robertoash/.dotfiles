-- Hybrid Colemak keyboard layout switcher for Kanata
-- Kanata sends: Colemak for single keys, QWERTY for modifiers
-- Reads layout from /tmp/active_keyboard_layout

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
		-- HYBRID MODE: Kanata sends Colemak for single keys, QWERTY for modifiers
		-- Perfect for keeping existing keybinds while getting Colemak movement

		local ok, langmapper = pcall(require, "langmapper")
		if ok then
			langmapper.setup({
				map_modes = { "n", "v" },
				map_filter = function(lhs, mode)
					-- Don't translate modifier combinations (Kanata handles those as QWERTY)
					if lhs:match("<[%w%-]+>") then
						return false
					end
					-- Only translate single character keys
					return #lhs == 1
				end,
				-- Swedish Colemak to QWERTY translation
				langmap = "fe,pr,gt,jy,lu,ui,yo,öp,rs,sd,tf,dg,nj,ek,il,oö,kn",
			})

			-- Fix the 3 displaced keys
			vim.keymap.set("n", "l", "i", { desc = "Insert mode (Colemak l→i)" })
			vim.keymap.set("n", "L", "I", { desc = "Insert at line start (Colemak L→I)" })
			vim.keymap.set("n", "j", "e", { desc = "End of word (Colemak j→e)" })
			vim.keymap.set("n", "J", "E", { desc = "End of WORD (Colemak J→E)" })
			vim.keymap.set("n", "k", "n", { desc = "Next search (Colemak k→n)" })
			vim.keymap.set("n", "K", "N", { desc = "Previous search (Colemak K→N)" })

			print("Colemak hybrid layout active (langmapper + displaced keys)")
		else
			-- Fallback without langmapper plugin
			vim.opt.langmap = "nj,ek,il" -- Essential movement only

			vim.keymap.set("n", "l", "i", { desc = "Insert mode (Colemak)" })
			vim.keymap.set("n", "L", "I", { desc = "Insert at line start (Colemak)" })
			vim.keymap.set("n", "k", "n", { desc = "Next search (Colemak)" })
			vim.keymap.set("n", "K", "N", { desc = "Previous search (Colemak)" })
			vim.keymap.set("n", "j", "e", { desc = "End of word (Colemak)" })
			vim.keymap.set("n", "J", "E", { desc = "End of WORD (Colemak)" })

			print("Colemak hybrid layout active (basic langmap fallback)")
		end
	elseif layout == "swe" then
		-- Swedish QWERTY - clear everything
		vim.opt.langmap = ""

		-- Remove displaced key mappings
		local displaced_keys = { "l", "L", "j", "J", "k", "K" }
		for _, key in ipairs(displaced_keys) do
			pcall(vim.keymap.del, "n", key)
		end

		-- Disable langmapper
		local ok, langmapper = pcall(require, "langmapper")
		if ok and langmapper.disable then
			langmapper.disable()
		end

		print("Swedish QWERTY layout active")
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
					setup_keyboard_layout()
					local new_layout = vim.g.detected_keyboard_layout

					if old_layout ~= new_layout then
						if new_layout == "cmk" then
							print("Switched to Colemak hybrid layout")
						elseif new_layout == "swe" then
							print("Switched to Swedish QWERTY layout")
						else
							print("Switched to " .. new_layout .. " layout")
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

-- Test command
vim.api.nvim_create_user_command("TestColemakLayout", function()
	local layout = vim.g.detected_keyboard_layout or "unknown"
	print("Current layout: " .. layout)

	if layout == "cmk" then
		print("✓ HYBRID COLEMAK ACTIVE")
		print("Movement: n(↓), e(↑), i(→), h(←)")
		print("Displaced: l(insert), k(next search), j(end word)")
		print("Keybinds: <leader>sf, <C-j> work as normal (QWERTY)")
		print("Hyprland: Uses QWERTY for Super+key combinations")
	elseif layout == "swe" then
		print("✓ SWEDISH QWERTY ACTIVE")
		print("Everything uses standard QWERTY positions")
	end
end, { desc = "Test current Colemak setup" })
