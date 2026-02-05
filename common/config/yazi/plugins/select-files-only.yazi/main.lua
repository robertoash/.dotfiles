-- Select all files (not directories) in current directory
return {
	entry = function(_, job)
		ya.manager_emit("escape", { visual = true })

		local files = cx.active.current.files
		for _, file in ipairs(files) do
			if not file.cha.is_dir then
				ya.manager_emit("toggle", { file.url })
			end
		end
	end,
}
