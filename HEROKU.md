# Heroku Deployment Optimizations

This document describes the optimizations made to reduce the LineupBoss Heroku slug size while maintaining build integrity.

## Optimization Strategy

The Heroku slug size optimization uses several complementary techniques:

1. **File Exclusion**: Unnecessary files are excluded from the slug using `.slugignore`
2. **Source Map Elimination**: Source maps are disabled in production builds
3. **Build Optimization**: A specialized build script optimizes the build process

## Implementation Files

1. **`.slugignore`**: Controls which files are included in the slug
   ```
   # Version control files
   .git
   .gitignore
   
   # Development files
   frontend/node_modules
   **/__pycache__
   **/*.pyc
   
   # Documentation and tests
   /docs
   **/*.md
   **/*.test.js
   ```

2. **`frontend/.env.production`**: Disables source map generation
   ```
   GENERATE_SOURCEMAP=false
   ```

3. **`bin/heroku_build.sh`**: Optimized build script
   ```bash
   # Install dependencies
   npm install --legacy-peer-deps --no-audit
   
   # Build frontend
   cd frontend && npm run build
   
   # Remove source maps
   find build -name "*.map" -delete
   
   # Install backend requirements
   pip install -r backend/requirements.txt
   ```

4. **`.npmrc`**: Streamlines npm behavior
   ```
   legacy-peer-deps=true
   audit=false
   fund=false
   ```

## Deployment Steps

1. These optimizations are automatically applied when deploying to Heroku:

   ```bash
   git push heroku main
   ```

2. To check your current slug size:

   ```bash
   heroku slugs:size
   ```

3. Monitor build logs to ensure everything works correctly:

   ```bash
   heroku logs --source app --tail
   ```

## Troubleshooting

If you encounter build issues:

1. Check Heroku build logs for specific errors
2. Verify the `bin/heroku_build.sh` script is executable (`chmod +x`)
3. Ensure the original public directory is properly included in the slug