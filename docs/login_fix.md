# Emergency Fix for Double API Prefix Login Issue

This document describes the emergency fix implemented to address the login issue caused by double API prefixes in the LineupBoss application.

## Issue Description

The frontend application was making API requests with a duplicate `/api` prefix, resulting in URLs like:
- `/api/api/auth/login` (instead of `/api/auth/login`)
- `/api/api/auth/me` (instead of `/api/auth/me`)

This caused HTTP 405 Method Not Allowed errors because these incorrect routes didn't exist in the backend.

## Two-Pronged Solution

We implemented a dual approach to fix this issue:

### 1. Frontend Fix

Added an enhanced `apiPath()` function in the frontend that:
- Detects and fixes double API prefixes (`/api/api/` → `/api/`)
- Works for all API endpoints
- Logs detailed information about path transformations
- Added extra safety handling for login specifically

However, this fix requires a redeployment of the frontend code, and there might be caching issues preventing it from taking effect immediately.

### 2. Backend Emergency Workaround

Added explicit route handlers in the backend to catch the problematic URLs:

```python
@app.route('/api/api/auth/login', methods=['POST'])
def fix_double_api_prefix_login():
    """Emergency fix for the /api/api/auth/login issue."""
    from api.auth import login as auth_login
    return auth_login()
```

Similar handlers were added for other critical endpoints:
- `/api/api/auth/register`
- `/api/api/auth/me`
- `/api/api/auth/refresh`
- `/api/api/user/profile`
- `/api/api/teams`

## Implementation Details

### Backend Workarounds

1. **Direct Route Handlers**: We've added explicit route handlers for the problematic double-prefixed endpoints, which forward the request to the correct blueprint handler.

2. **Logging**: Added detailed logging to track when these emergency handlers are used.

### Frontend Fixes

1. **Path Normalization**: Enhanced the `apiPath` function to handle and correct double prefixes.

2. **Login Function Enhancement**: Added extra safety checking in the login function.

3. **Debug Logging**: Added logging to help diagnose issues with path handling.

## Testing

To test if the fix is working:

1. Try logging in to the application
2. Check the browser console for `[API-DEBUG]` messages that indicate path handling
3. Check the server logs for `[API] EMERGENCY FIX` messages that indicate the backend fix was triggered

## Long-term Solution

The emergency fix is a temporary measure. The long-term solution is to:

1. Ensure the frontend apiPath function correctly handles all URL paths
2. Implement a consistent and standardized approach to route handling across the application
3. Remove the emergency handlers once the frontend fix is fully deployed and tested

## Affected Files

- `/backend/app.py` - Added emergency route handlers
- `/frontend/src/services/api.js` - Enhanced apiPath function and login method