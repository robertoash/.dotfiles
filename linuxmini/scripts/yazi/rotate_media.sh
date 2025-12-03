#!/bin/bash

# rotate-media.sh - Rotate images and videos clockwise or counterclockwise
# Usage: rotate-media.sh --cw|--ccw file1 [file2 ...]

show_help() {
    echo "Usage: $0 --cw|--ccw file1 [file2 ...]"
    echo ""
    echo "Options:"
    echo "  --cw   Rotate clockwise (90 degrees)"
    echo "  --ccw  Rotate counterclockwise (-90 degrees)"
    echo ""
    echo "Supported formats:"
    echo "  Images: jpg, jpeg, png, gif, bmp, tiff, webp"
    echo "  Videos: mp4, mkv, avi, mov, wmv, flv, webm, m4v"
    exit 1
}

# Check if required tools are installed
check_dependencies() {
    if ! command -v magick >/dev/null 2>&1; then
        echo "Error: ImageMagick (magick command) is not installed"
        echo "Install with: brew install imagemagick  # macOS"
        echo "           or: sudo apt install imagemagick  # Ubuntu/Debian"
        exit 1
    fi
    
    if ! command -v ffmpeg >/dev/null 2>&1; then
        echo "Error: FFmpeg is not installed"
        echo "Install with: brew install ffmpeg  # macOS"
        echo "           or: sudo apt install ffmpeg  # Ubuntu/Debian"
        exit 1
    fi
}

# Determine file type based on extension
get_file_type() {
    local file="$1"
    local ext="${file##*.}"
    ext=$(echo "$ext" | tr '[:upper:]' '[:lower:]')
    
    case "$ext" in
        jpg|jpeg|png|gif|bmp|tiff|tif|webp)
            echo "image"
            ;;
        mp4|mkv|avi|mov|wmv|flv|webm|m4v|mpg|mpeg)
            echo "video"
            ;;
        *)
            echo "unknown"
            ;;
    esac
}

# Rotate image using ImageMagick
rotate_image() {
    local file="$1"
    local direction="$2"
    local degrees
    
    if [ "$direction" = "--cw" ]; then
        degrees="90"
    else
        degrees="-90"
    fi
    
    echo "Rotating image: $file (${degrees}°)"
    if magick "$file" -rotate "$degrees" "$file"; then
        echo "✓ Successfully rotated $file"
    else
        echo "✗ Failed to rotate $file"
        return 1
    fi
}

# Rotate video using FFmpeg
rotate_video() {
    local file="$1"
    local direction="$2"
    local transpose_value
    local temp_file="${file%.*}_temp.${file##*.}"
    
    # FFmpeg transpose values:
    # 0 = 90° counterclockwise and vertical flip
    # 1 = 90° clockwise
    # 2 = 90° counterclockwise  
    # 3 = 90° clockwise and vertical flip
    
    if [ "$direction" = "--cw" ]; then
        transpose_value="1"
    else
        transpose_value="2"
    fi
    
    echo "Rotating video: $file (this may take a while...)"
    if ffmpeg -i "$file" -vf "transpose=$transpose_value" -c:a copy "$temp_file" -y >/dev/null 2>&1; then
        if mv "$temp_file" "$file"; then
            echo "✓ Successfully rotated $file"
        else
            echo "✗ Failed to replace original file"
            rm -f "$temp_file"
            return 1
        fi
    else
        echo "✗ Failed to rotate $file"
        rm -f "$temp_file"
        return 1
    fi
}

# Main function
main() {
    # Check arguments
    if [ $# -lt 2 ]; then
        show_help
    fi
    
    local direction="$1"
    shift
    
    # Validate direction argument
    if [ "$direction" != "--cw" ] && [ "$direction" != "--ccw" ]; then
        echo "Error: First argument must be --cw or --ccw"
        show_help
    fi
    
    # Check dependencies
    check_dependencies
    
    # Process each file
    local failed_count=0
    local success_count=0
    
    for file in "$@"; do
        if [ ! -f "$file" ]; then
            echo "✗ File not found: $file"
            ((failed_count++))
            continue
        fi
        
        local file_type=$(get_file_type "$file")
        
        case "$file_type" in
            image)
                if rotate_image "$file" "$direction"; then
                    ((success_count++))
                else
                    ((failed_count++))
                fi
                ;;
            video)
                if rotate_video "$file" "$direction"; then
                    ((success_count++))
                else
                    ((failed_count++))
                fi
                ;;
            unknown)
                echo "✗ Unsupported file type: $file"
                ((failed_count++))
                ;;
        esac
    done
    
    # Summary
    echo ""
    echo "Summary: $success_count successful, $failed_count failed"
    
    if [ $failed_count -gt 0 ]; then
        exit 1
    fi
}

# Run main function with all arguments
main "$@"
