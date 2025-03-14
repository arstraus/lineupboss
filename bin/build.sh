#!/bin/bash
set -e

# Set npm config settings
npm config set legacy-peer-deps true

# Go to frontend directory
cd frontend

# Delete existing node_modules to ensure a clean install
if [ -d "node_modules" ]; then
  rm -rf node_modules
fi

# Delete package-lock.json to ensure a clean install
if [ -f "package-lock.json" ]; then
  rm -f package-lock.json
fi

# Directly modify package.json to use React 18
sed -i 's/"react": ".*"/"react": "18.0.0"/g' package.json
sed -i 's/"react-dom": ".*"/"react-dom": "18.0.0"/g' package.json

# Install dependencies with legacy-peer-deps flag
npm install --legacy-peer-deps

# Build the application
npm run build