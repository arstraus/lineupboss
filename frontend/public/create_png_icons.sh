#!/bin/bash

# This script creates PNG versions of our SVG icons
# Requirements: 
# - You need to have ImageMagick installed
# - Install with: brew install imagemagick (MacOS) or apt-get install imagemagick (Linux)

# Create PNG versions of baseball favicon
echo "Creating PNG icons from baseball-favicon.svg..."
convert -background transparent baseball-favicon.svg -resize 192x192 baseball-logo192.png
convert -background transparent baseball-favicon.svg -resize 512x512 baseball-logo512.png

# Create PNG versions of baseball-LB favicon
echo "Creating PNG icons from baseball-lb-favicon.svg..."
convert -background transparent baseball-lb-favicon.svg -resize 192x192 baseball-lb-logo192.png
convert -background transparent baseball-lb-favicon.svg -resize 512x512 baseball-lb-logo512.png

# Create PNG versions of baseball diamond favicon
echo "Creating PNG icons from baseball-diamond-favicon.svg..."
convert -background transparent baseball-diamond-favicon.svg -resize 192x192 baseball-diamond-logo192.png
convert -background transparent baseball-diamond-favicon.svg -resize 512x512 baseball-diamond-logo512.png

echo "PNG icons creation complete."
echo "To use a specific icon set, update the manifest.json and index.html files."