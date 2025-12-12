#!/usr/bin/env bash
# Space click handler - switches to the specified space number
# Usage: space_click.sh <space_number>

SPACE_NUM=$1

# Get all spaces in order: sort screens right-to-left, then spaces per screen
# This matches macOS's space numbering (spaces on rightmost monitor come first)
hs -c "
local allSpaces = hs.spaces.allSpaces()
local screens = hs.screen.allScreens()
table.sort(screens, function(a, b) return a:frame().x > b:frame().x end)
local spacesList = {}
for _, screen in ipairs(screens) do
  local screenSpaces = allSpaces[screen:getUUID()]
  if screenSpaces then
    for _, spaceId in ipairs(screenSpaces) do
      table.insert(spacesList, spaceId)
    end
  end
end
if spacesList[$SPACE_NUM] then
  hs.spaces.gotoSpace(spacesList[$SPACE_NUM])
end
" &
