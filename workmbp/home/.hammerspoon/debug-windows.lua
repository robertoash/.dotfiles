-- Debug script to compare window properties
-- Run this in Hammerspoon console

local function inspect_window(win)
    if not win then
        print("No window provided")
        return
    end

    print("\n=== Window: " .. (win:title() or "unknown") .. " ===")
    print("ID: " .. tostring(win:id()))
    print("Application: " .. (win:application() and win:application():name() or "unknown"))

    -- Window properties
    print("\nWindow Properties:")
    print("  isStandard: " .. tostring(win:isStandard()))
    print("  isVisible: " .. tostring(win:isVisible()))
    print("  isFullScreen: " .. tostring(win:isFullScreen()))
    print("  isMinimized: " .. tostring(win:isMinimized()))

    -- Frame info
    local frame = win:frame()
    print("\nFrame:")
    print(string.format("  x=%.0f, y=%.0f, w=%.0f, h=%.0f", frame.x, frame.y, frame.w, frame.h))

    -- Screen
    local screen = win:screen()
    print("\nScreen: " .. (screen and screen:name() or "none"))

    -- Window role and subrole
    print("\nAccessibility:")
    local success, role = pcall(function() return win:role() end)
    print("  role: " .. (success and role or "error"))

    local success2, subrole = pcall(function() return win:subrole() end)
    print("  subrole: " .. (success2 and subrole or "error"))

    -- Check window filter status
    print("\nWindow Filter Test:")
    local filter = hs.window.filter.new()
    filter:setDefaultFilter({})
    local allowed = filter:isWindowAllowed(win)
    print("  Allowed by default filter: " .. tostring(allowed))

    print("\n")
end

-- Get all WezTerm windows
print("=== ALL WEZTERM WINDOWS ===")
local all_windows = hs.window.allWindows()
for _, win in ipairs(all_windows) do
    local app = win:application()
    if app and app:name() == "WezTerm" then
        inspect_window(win)
    end
end

print("\n=== To inspect a specific window, run: ===")
print("inspect_window(hs.window.focusedWindow())")
