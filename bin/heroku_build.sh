#!/bin/bash
set -e

# Heroku-optimized build script for LineupBoss
echo "===== Starting Heroku Build ====="

# Go to frontend directory
cd frontend
echo "Building frontend..."

# Install frontend dependencies
npm install --legacy-peer-deps --no-audit --no-fund

# Build with sourcemaps disabled via .env.production
NODE_ENV=production npm run build

# Remove any source maps that might have been generated
find build -name "*.map" -type f -delete

# Return to root directory
cd ..

# Install backend requirements
echo "Installing backend requirements..."
pip install -r backend/requirements.txt

# Print build info
echo "Build complete. Sizes:"
du -sh frontend/build backend 2>/dev/null || true

echo "===== Heroku Build Complete ====="