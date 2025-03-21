#!/bin/bash
set -e

# Heroku-optimized build script for LineupBoss
echo "===== Starting Heroku Build ====="

# Go to frontend directory
cd frontend
echo "Building frontend..."

# Install frontend dependencies
echo "Installing frontend dependencies including recharts..."
npm install --legacy-peer-deps --no-audit --no-fund
# Explicitly install recharts to be sure it's available
npm install --legacy-peer-deps --no-audit --no-fund recharts

# Ensure source maps are disabled
echo "GENERATE_SOURCEMAP=false" > .env.production

# Build with sourcemaps disabled
NODE_ENV=production npm run build

# Simple source map removal
echo "Removing source maps..."
find build -name "*.map" -type f -delete

# Make JS files smaller by removing sourcemap references
echo "Optimizing JS bundle sizes..."
find build -name "*.js" -exec sed -i.bak 's/\/\/# sourceMappingURL=.*\.map//g' {} \;
find build -name "*.js.bak" -delete

# Print build info
echo "Frontend build complete. Size:"
du -sh build 2>/dev/null || true

# Return to project root
cd ..

# Do NOT remove node_modules as it breaks the build process
# Do NOT remove cache files as they may be needed

echo "===== Heroku Build Complete ====="

# We don't install backend requirements here because the Python buildpack 
# will handle that automatically after the Node.js buildpack completes