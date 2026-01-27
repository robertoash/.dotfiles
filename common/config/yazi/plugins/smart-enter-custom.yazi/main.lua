--- Smart enter with ISO burn support
--- Checks for .iso files and launches burn plugin, otherwise delegates to smart-enter

local function setup(self, opts)
	self.open_multi = opts and opts.open_multi
end

local function entry(self)
	local h = cx.active.current.hovered

	-- Check if it's an ISO file
	if h and not h.cha.is_dir and tostring(h.url):match("%.iso$") then
		ya.manager_emit("plugin", { "burn" })
		return
	end

	-- Otherwise, delegate to original smart-enter behavior
	ya.emit(h and h.cha.is_dir and "enter" or "open", { hovered = not self.open_multi })
end

return { entry = entry, setup = setup }
