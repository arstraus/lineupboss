#!/bin/bash
set -e

# Set npm config settings
npm config set legacy-peer-deps true

# Go to frontend directory
cd frontend

# Always do a clean install to ensure all dependencies are properly installed
echo "Installing dependencies..."
# Install dependencies with legacy-peer-deps flag and production flag
npm install --legacy-peer-deps --production --no-audit --no-fund

# Directly modify package.json to use React 18 if needed
if grep -q "\"react\": \"18.0.0\"" package.json; then
  echo "React 18 already configured"
else
  echo "Configuring React 18..."
  sed -i 's/"react": ".*"/"react": "18.0.0"/g' package.json
  sed -i 's/"react-dom": ".*"/"react-dom": "18.0.0"/g' package.json
fi

# Build the application
echo "Building React application..."
export NODE_ENV=production
npm run build --production

# Remove source maps to reduce build size
echo "Removing source maps to reduce build size..."
find build -name "*.map" -delete

# Clean up development dependencies after build
echo "Cleaning up node_modules..."
rm -rf node_modules