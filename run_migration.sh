#!/bin/bash

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "DATABASE_URL environment variable is not set. Please set it before running migrations."
    exit 1
fi

# Execute the migration
echo "Running migration to update user address fields..."
python3 backend/migrations/update_user_address_fields.py

# Return the result
if [ $? -eq 0 ]; then
    echo "Migration completed successfully!"
else
    echo "Migration failed. Please check the logs."
    exit 1
fi

echo "Done."