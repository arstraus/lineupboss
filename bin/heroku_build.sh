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

# Print build info
echo "Frontend build complete. Size:"
du -sh build 2>/dev/null || true

echo "===== Frontend Build Complete ====="

# We don't install backend requirements here because the Python buildpack 
# will handle that automatically after the Node.js buildpack completes