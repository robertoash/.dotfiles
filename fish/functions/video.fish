function vid_q
  set -l file "$argvtest 1"

  # Extract the width and height using ffprobe
  set -l width $(ffprobe -v error -select_streams v:0 -show_entries stream=width -of csv=p=0 "$file")
  set -l height $(ffprobe -v error -select_streams v:0 -show_entries stream=height -of csv=p=0 "$file")

  # Compare width and height
  if (( width > height ))
    echo "$height"  # Horizontal: return height
  else
    echo "$width"   # Vertical: return width
  fi
end
