# Heroku Slug Size Optimization

This document explains the changes made to reduce the Heroku slug size for LineupBoss.

## Changes Made

1. **Added .slugignore file**
   - Excludes development files and directories not needed for runtime
   - Prevents source code, documentation, and dev dependencies from being included in the slug

2. **Updated build.sh script**
   - Added `--production` flag to npm install
   - Removes source maps from build output
   - Cleans up node_modules after build to reduce slug size

3. **Added .npmrc file**
   - Forces production mode for npm
   - Disables unnecessary features during build
   - Ensures consistent dependency installation

4. **Created .env.production file**
   - Disables source map generation for production builds
   - Sets production API URL

5. **Added .buildpacks file**
   - Explicitly specifies buildpack order for multi-buildpack setups

6. **Updated package.json**
   - Added resolutions field to enforce consistent dependency versions
   - Helps reduce duplicate dependencies

## Deployment Instructions

1. **Commit and push these changes**
   ```bash
   git add .
   git commit -m "Optimize Heroku slug size"
   git push heroku main
   ```

2. **After deployment, check the slug size**
   ```bash
   heroku slugs:size
   ```

3. **Review build logs for any issues**
   ```bash
   heroku logs --source app --tail
   ```

## Additional Optimization Tips

If the slug size is still too large after these changes, consider these additional steps:

1. **Use Heroku's node_prune buildpack**
   ```bash
   heroku buildpacks:add --index 2 https://github.com/heroku/heroku-buildpack-node-prune.git
   ```

2. **Consider splitting the application**
   - Separate the frontend and backend into different Heroku apps
   - Use Heroku's free static site hosting for the frontend

3. **Use a CDN for static assets**
   - Move large assets to a CDN like Cloudinary or Amazon S3
   - Reference them by URL in your application

4. **Clean temporary files during build**
   - Add additional cleanup commands to the build script
   - Remove any temporary files created during the build process

## Monitoring Slug Size

To monitor your slug size over time:

```bash
heroku slugs
```

This shows a history of your application's slugs and their sizes.