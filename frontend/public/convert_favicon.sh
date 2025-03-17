#!/bin/bash

# This script converts SVG files to ICO format
# Requirements: 
# - You need to have ImageMagick installed
# - You can install it with: brew install imagemagick (MacOS) or apt-get install imagemagick (Linux)

# Convert baseball-favicon.svg to favicon.ico
echo "Converting baseball-favicon.svg to favicon.ico..."
convert -background transparent baseball-favicon.svg -define icon:auto-resize=16,32,48,64 favicon.ico

# Convert baseball-lb-favicon.svg to favicon-lb.ico
echo "Converting baseball-lb-favicon.svg to favicon-lb.ico..."
convert -background transparent baseball-lb-favicon.svg -define icon:auto-resize=16,32,48,64 favicon-lb.ico

# Convert baseball-diamond-favicon.svg to favicon-diamond.ico
echo "Converting baseball-diamond-favicon.svg to favicon-diamond.ico..."
convert -background transparent baseball-diamond-favicon.svg -define icon:auto-resize=16,32,48,64 favicon-diamond.ico

echo "Conversion complete. Please make sure you have chosen the favicon you want."
echo "To use a specific favicon, update the <link rel=\"icon\"> tag in index.html"