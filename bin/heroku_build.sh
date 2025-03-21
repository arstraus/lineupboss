#!/bin/bash
set -e

# Heroku-optimized build script for LineupBoss
echo "===== Starting Heroku Build ====="

# Go to frontend directory
cd frontend
echo "Building frontend..."

# Install frontend dependencies
npm install --legacy-peer-deps --no-audit --no-fund

# Ensure source maps are disabled in multiple ways
echo "GENERATE_SOURCEMAP=false" > .env.production
echo "INLINE_RUNTIME_CHUNK=false" >> .env.production

# Build with sourcemaps disabled
NODE_ENV=production npm run build

# Aggressive source map removal (multiple patterns)
echo "Removing source maps..."
find build -name "*.map" -type f -delete
find build -path "*/static/js/*.js.map" -delete
find build -path "*/static/css/*.css.map" -delete

# Make JS files smaller by removing comments and unnecessary whitespace
echo "Optimizing JS bundle sizes..."
find build -name "*.js" -exec sed -i.bak 's/\/\/# sourceMappingURL=.*\.map//g' {} \;
find build -name "*.js.bak" -delete

# Print build info
echo "Frontend build complete. Size:"
du -sh build 2>/dev/null || true

# Return to project root
cd ..

# Remove node_modules to drastically reduce slug size
echo "Removing node_modules from slug..."
rm -rf frontend/node_modules

# Remove any temporary or cache directories 
echo "Cleaning up cache directories..."
rm -rf frontend/.cache
rm -rf frontend/.npm

echo "Final build sizes:"
du -sh frontend 2>/dev/null || true
du -sh frontend/build 2>/dev/null || true

echo "===== Heroku Build Complete ====="

# We don't install backend requirements here because the Python buildpack 
# will handle that automatically after the Node.js buildpack completes