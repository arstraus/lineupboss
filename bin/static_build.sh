#!/bin/bash
set -e

echo "===== Starting Static Build Process ====="

# Create backend static directory
if [ ! -d "backend/static" ]; then
  echo "Creating backend/static directory"
  mkdir -p backend/static
fi

# Check if we already have a frontend build
if [ -d "frontend/build" ]; then
  echo "Frontend build exists, copying to backend/static"
  cp -R frontend/build/* backend/static/
  echo "Static files copied to backend/static"
else
  echo "No frontend build found, attempting to create one"
  
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
  
  # Copy build files to backend/static
  echo "Copying build files to backend/static"
  cd ..
  cp -R frontend/build/* backend/static/
  echo "Static files copied to backend/static"
fi

# Install backend requirements
echo "Installing backend requirements..."
pip install -r backend/requirements.txt

echo "===== Static Build Process Complete ====="