vid_q() {
  local file="$1"

  # Extract the width and height using ffprobe
  local width=$(ffprobe -v error -select_streams v:0 -show_entries stream=width -of csv=p=0 "$file")
  local height=$(ffprobe -v error -select_streams v:0 -show_entries stream=height -of csv=p=0 "$file")

  # Compare width and height
  if (( width > height )); then
    echo "$height"  # Horizontal: return height
  else
    echo "$width"   # Vertical: return width
  fi
}
