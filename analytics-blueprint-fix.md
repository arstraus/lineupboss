# Analytics Blueprint Registration Fix

This document outlines the changes needed to fix the RESTful analytics endpoints in LineupBoss.

## Issue Identified

Based on testing with the `test-analytics-heroku.js` script, we've confirmed:

1. The legacy analytics endpoints (e.g., `/api/analytics/teams/{teamId}/analytics`) work correctly
2. The RESTful analytics endpoints (e.g., `/api/analytics/teams/{teamId}`) are not accessible
3. The debug endpoint shows `"analytics_registered": false`

The root cause is that the analytics blueprint containing the RESTful endpoints is not being properly registered in the application.

## Changes Implemented

### 1. Enhanced `analytics/__init__.py`

```python
"""
Analytics module initialization.

This module exports the analytics blueprint for RESTful API endpoints.
"""
# Import the routes module to ensure all routes are defined
from api.analytics.routes import analytics_bp

# Export the blueprint for import by the main API module
__all__ = ['analytics_bp']
```

### 2. Improved Blueprint Registration in `api/__init__.py`

```python
# Register analytics blueprint (for team and player analytics)
try:
    # First try to import from the routes.py in the analytics package
    try:
        from api.analytics.routes import analytics_bp
        api.register_blueprint(analytics_bp, url_prefix='/analytics')
        print(f"SUCCESS: Registered RESTful analytics blueprint with URL prefix /analytics")
        analytics_registered = True
    except ImportError as e:
        print(f"WARNING: Could not import from api.analytics.routes: {e}")
        
        # Fallback to the analytics.py module if the package structure fails
        try:
            from api.analytics import analytics_bp
            api.register_blueprint(analytics_bp, url_prefix='/analytics')
            print(f"SUCCESS: Registered legacy analytics blueprint with URL prefix /analytics")
            analytics_registered = True
        except Exception as e:
            print(f"ERROR: Analytics blueprint fallback registration failed: {e}")
            analytics_registered = False
except Exception as e:
    print(f"GENERAL ERROR: Error registering analytics blueprint: {e}")
    print(f"Stack trace: {traceback.format_exc()}")
    analytics_registered = False
```

### 3. Updated Analytics Endpoints in `analytics.py`

We've added the RESTful endpoint patterns directly to `analytics.py` as well to ensure both the legacy package structure and the new RESTful structure will work:

```python
@analytics_bp.route('/teams/<int:team_id>/players/batting', methods=['GET'])
@jwt_required
def get_player_batting_analytics(team_id):
    """
    Get batting analytics for all players in a team using RESTful pattern.
    """
    return get_team_batting_analytics(team_id)

@analytics_bp.route('/teams/<int:team_id>/players/fielding', methods=['GET'])
@jwt_required
def get_player_fielding_analytics(team_id):
    """
    Get fielding analytics for all players in a team using RESTful pattern.
    """
    return get_team_fielding_analytics(team_id)

@analytics_bp.route('/teams/<int:team_id>', methods=['GET'])
@jwt_required
def get_team_analytics_restful(team_id):
    """
    Get team analytics across all games using RESTful pattern.
    """
    return get_team_analytics(team_id)
```

## Testing

The changes have been tested locally and a script (`test-analytics-heroku.js`) has been created to test the endpoints after deployment. This script:

1. Tests basic API connectivity
2. Checks the analytics status endpoint
3. Tests both legacy and RESTful endpoints
4. Compares results across multiple URL patterns

## Next Steps

1. Deploy these changes to Heroku
2. Run the test script against the updated deployment to verify the RESTful endpoints are now accessible
3. Update the API documentation to include the standardized RESTful endpoints