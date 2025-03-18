# Token Refresh Mechanism Documentation

## Overview

LineupBoss implements a token refresh system to provide a seamless authentication experience. The system automatically refreshes JSON Web Tokens (JWTs) before they expire, preventing users from being logged out unexpectedly.

## Backend Implementation

### Endpoints

- `POST /api/auth/refresh`: Refreshes the access token if it's about to expire
- `GET /api/auth/me`: Returns user info with token expiration status

### Token Lifecycle

1. **Token Creation**: When a user logs in or registers, they receive a JWT with a 15-day expiration.
2. **Token Refresh Window**: A token is eligible for refresh when it's within 7 days of expiring.
3. **Refresh Process**: The refresh endpoint validates the current token and issues a new one with a fresh 15-day expiration.

### Security Considerations

- The refresh mechanism requires a valid token for authentication
- Tokens are validated before refreshing
- User status is verified before issuing new tokens (accounts must be approved)
- No refresh tokens are stored server-side

## Frontend Implementation

### Automatic Refresh Triggers

The frontend implements three mechanisms to refresh tokens:

1. **Response Interceptor**: Detects the `token_expires_soon` flag from `/auth/me` responses and triggers a refresh
2. **401 Response Handler**: Attempts to refresh the token when receiving 401 unauthorized errors
3. **Background Timer**: Checks token status every 15 minutes as a safety mechanism

### Refresh Process

1. The frontend detects that a token needs refreshing
2. It calls the `/auth/refresh` endpoint with the current token
3. If successful, it updates the token in local storage
4. The updated token is used for subsequent requests

### Error Handling

- Failed refresh attempts that return 401 will trigger logout
- Multiple simultaneous refresh attempts are prevented
- Network errors during refresh are logged but don't force logout

## Integration Guide

### Making API Calls

All authenticated API calls should use the axios interceptor, which:

1. Automatically adds the latest token from localStorage
2. Handles token refresh when needed
3. Retries failed requests after successful token refresh

### Refresh Scenarios

- **Proactive Refresh**: Token is refreshed when `/auth/me` indicates it's expiring soon
- **Reactive Refresh**: Token is refreshed when any API call returns a 401 unauthorized error
- **Periodic Refresh**: Token freshness is verified every 15 minutes

## Testing

To test the token refresh functionality:

1. Log in to the application
2. In browser devtools, edit the token in localStorage to have an earlier exp date
3. Perform an API call that requires authentication
4. Verify that the token is refreshed automatically

## API Path Architecture

LineupBoss has a standardized API architecture:

1. **Blueprint-Based Routes**: API endpoints are registered using Flask Blueprints with prefixes:
   - `/api/` - System endpoints (root, health checks, test endpoints)
   - `/api/auth/` - Authentication endpoints
   - `/api/user/` - User profile endpoints
   - `/api/teams/` - Team management 
   - `/api/players/` - Player management
   - `/api/games/` - Game management
   - `/api/admin/` - Admin functions
   - `/api/docs/` - API documentation

2. **Frontend Path Normalization**: 
   - The frontend `apiPath()` function ensures all API calls have the correct `/api` prefix
   - This function actively detects and corrects duplicate prefixes (`/api/api/`)
   - Logs original vs. processed paths to help with debugging

3. **Backward Compatibility**:
   - Legacy direct routes in app.py are maintained with deprecation warnings
   - These routes forward requests to the blueprint endpoints
   - They will be removed in a future release

### Deprecated Routes

The following routes are deprecated and will be removed in a future release:
- `/api` - Root endpoint (use `/api/` system blueprint route instead)
- `/api/test-jwt` - JWT test endpoint (use `/api/test-jwt` system blueprint route)
- `/api/test-db` - Database test endpoint (use `/api/test-db` system blueprint route)
- `/api/user/profile` - User profile endpoints (use `/api/user/profile` blueprint route)
- `/api/user/password` - Password update endpoint (use `/api/user/password` blueprint route)
- `/api/user/subscription` - Subscription endpoint (use `/api/user/subscription` blueprint route)

> **Note**: These routes function identically to their blueprint counterparts, but generate deprecation warnings in the server logs.

## Implementation Details for LineupBoss

### Configuration Constants

The token refresh system uses the following constants (defined in `api/auth.py`):

- `ACCESS_TOKEN_EXPIRES = timedelta(days=15)`: Duration of freshly issued tokens
- `REFRESH_MARGIN = timedelta(days=7)`: Window before expiration when tokens become eligible for refresh

### Database Interaction

The token refresh system is stateless and doesn't require any database writes:
- The `/auth/me` endpoint uses `read_only=True` when accessing the database
- The `/auth/refresh` endpoint only writes to the database if user data needs to be updated

### Refresh Logic Flow

1. Frontend requests user info via `/auth/me`
2. Backend calculates token expiration and adds `token_expires_soon` flag if needed
3. Frontend detects the flag and calls `/auth/refresh`
4. Backend verifies the current token and issues a new one
5. Frontend stores the new token and uses it for subsequent requests

### Key Files

- **Backend**: 
  - `/backend/api/auth.py`: Contains refresh endpoint implementation
  - `/backend/services/auth_service.py`: Contains token creation logic

- **Frontend**:
  - `/frontend/src/services/api.js`: Contains axios interceptors for token handling
  - `/frontend/src/services/AuthContext.js`: Manages auth state including token refresh

## Troubleshooting

### Common Issues

**Issue**: Users being logged out unexpectedly  
**Solution**: Check if the token_expires_soon flag is being correctly set and detected. Verify the refresh API call is succeeding.

**Issue**: Multiple token refresh requests happening simultaneously  
**Solution**: The frontend includes an `isRefreshing` flag to prevent this, but check the browser console for related errors.

**Issue**: Refresh working in development but not production  
**Solution**: Verify environment configuration, especially concerning CORS settings and API base URLs.

**Issue**: "405 Method Not Allowed" errors during login/refresh  
**Solution**: This often indicates a duplicate API path prefix (/api/api/). Check the request URL in browser dev tools. The apiPath function has been enhanced to detect and fix this issue automatically.

**Issue**: API calls fail with unexpected paths  
**Solution**: The enhanced apiPath function now normalizes paths, preventing issues like double slashes or missing prefixes. Check the browser console logs for "original" vs. processed paths to troubleshoot.

### Debugging Tools

- Use your browser's Network tab to monitor `/auth/refresh` calls
- Check localStorage in your browser to inspect token contents
- Enable debug logging by setting `process.env.NODE_ENV = 'development'`