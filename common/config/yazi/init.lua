-- ~/.config/yazi/init.lua

-- smart-enter plugin (unused now, burn plugin handles Enter)
require("smart-enter"):setup({
	open_multi = false,
})

require("relative-motions"):setup({
	show_numbers = "relative",
	show_motion = true,
	enter_mode = "first",
})

require("sshfs"):setup({
	sshfs_options = {
		"reconnect",
		"compression=yes",
		"ServerAliveInterval=15",
		"ServerAliveCountMax=3",
		"allow_other",
	},
})

require("bunny"):setup({
	hops = {
		{ key = "/", path = "/" },
		{ key = "t", path = "/tmp" },
		{ key = "~", path = "~", desc = "Home" },
		{ key = "c", path = "~/.config", desc = "Config files" },
		{ key = { "l", "s" }, path = "~/.local/share", desc = "Local share" },
		{ key = { "l", "b" }, path = "~/.local/bin", desc = "Local bin" },
		{ key = { "l", "t" }, path = "~/.local/state", desc = "Local state" },
		-- key and path attributes are required, desc is optional
	},
	desc_strategy = "path", -- If desc isn't present, use "path" or "filename", default is "path"
	ephemeral = true, -- Enable ephemeral hops, default is true
	tabs = true, -- Enable tab hops, default is true
	notify = false, -- Notify after hopping, default is false
	fuzzy_cmd = "fzf", -- Fuzzy searching command, default is "fzf"
})

require("full-border"):setup({
	-- Available values: ui.Border.PLAIN, ui.Border.ROUNDED
	type = ui.Border.ROUNDED,
})
