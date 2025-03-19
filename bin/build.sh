#!/bin/bash
set -e

echo "===== Starting Build Process ====="

# Go to frontend directory
cd frontend
echo "Changed to frontend directory: $(pwd)"

# Install frontend dependencies
echo "Installing frontend dependencies..."
npm install --legacy-peer-deps

# Build the frontend
echo "Building React application..."
npm run build

# Remove source maps to reduce size
echo "Removing source maps to reduce size..."
find build -name "*.map" -type f -delete

# Install backend requirements
echo "Installing backend requirements..."
cd ..
pip install -r backend/requirements.txt

echo "===== Build Process Complete ====="