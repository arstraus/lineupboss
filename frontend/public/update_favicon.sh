#!/bin/bash

# Master script for updating LineupBoss app icons
# This script requires ImageMagick to be installed

# Check if ImageMagick is installed
if ! command -v convert &> /dev/null; then
    echo "ImageMagick is not installed. Please install it first."
    echo "On macOS: brew install imagemagick"
    echo "On Linux: apt-get install imagemagick"
    exit 1
fi

# Make the scripts executable
chmod +x convert_favicon.sh
chmod +x create_png_icons.sh

# Run the conversion scripts
echo "=== Converting SVG to ICO files ==="
./convert_favicon.sh

echo ""
echo "=== Creating PNG files from SVG ==="
./create_png_icons.sh

echo ""
echo "=== Favicon Update Complete ==="
echo "Three favicon options have been created:"
echo "1. favicon.ico (baseball with seams)"
echo "2. favicon-lb.ico (baseball with 'LB' text)"
echo "3. favicon-diamond.ico (baseball diamond)"
echo ""
echo "To use a specific favicon:"
echo "1. Rename your chosen favicon to 'favicon.ico'"
echo "2. For app icons, update manifest.json to use the matching PNG files"
echo ""
echo "Example for using the baseball-lb version:"
echo "cp favicon-lb.ico favicon.ico"
echo "cp baseball-lb-logo192.png logo192.png"
echo "cp baseball-lb-logo512.png logo512.png"
echo ""
echo "Note: After deployment, you may need to clear your browser cache to see the changes."