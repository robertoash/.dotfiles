--- @sync entry

local function entry()
	local files = cx.active.current.files

	-- Deselect everything first
	ya.emit("escape", {})

	-- Select each file (not directories)
	for _, file in ipairs(files) do
		if not file.cha.is_dir then
			ya.emit("toggle", { file.url })
		end
	end
end

return { entry = entry }
