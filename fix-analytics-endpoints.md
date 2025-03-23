# Comprehensive Fix for RESTful Analytics Endpoints

After testing, we've confirmed that the RESTful analytics endpoints are still not working. Here's a comprehensive fix that should resolve the issue.

## Current Status

- Basic connectivity to the API is working
- Legacy analytics endpoints (e.g., `/api/analytics/teams/{teamId}/analytics`) work correctly
- RESTful analytics endpoints (e.g., `/api/analytics/teams/{teamId}`) are returning 404 errors
- The analytics blueprint is not being properly registered

## Detailed Fix Implementation

### 1. Verify Required Files

Make sure these files exist and have the correct content:

- `/backend/api/analytics/__init__.py`
- `/backend/api/analytics/routes.py`

### 2. Direct Endpoint Registration in App.py

Add direct endpoint registrations in `app.py` to ensure the RESTful endpoints work regardless of blueprint registration issues:

```python
# Add direct RESTful analytics endpoints as fallback
@app.route('/api/analytics/teams/<int:team_id>', methods=['GET'])
@jwt_required()
def direct_team_analytics_restful(team_id):
    """Direct RESTful team analytics endpoint if blueprint fails"""
    try:
        from services.analytics_service import AnalyticsService
        analytics = AnalyticsService.get_team_analytics(team_id)
        return jsonify(analytics), 200
    except Exception as e:
        return jsonify({"error": f"Failed to get team analytics: {str(e)}"}), 500

@app.route('/api/analytics/teams/<int:team_id>/players/batting', methods=['GET'])
@jwt_required()
def direct_player_batting_analytics(team_id):
    """Direct RESTful player batting analytics endpoint if blueprint fails"""
    try:
        from services.analytics_service import AnalyticsService
        analytics = AnalyticsService.get_player_batting_analytics(team_id)
        return jsonify(analytics), 200
    except Exception as e:
        return jsonify({"error": f"Failed to get player batting analytics: {str(e)}"}), 500

@app.route('/api/analytics/teams/<int:team_id>/players/fielding', methods=['GET'])
@jwt_required()
def direct_player_fielding_analytics(team_id):
    """Direct RESTful player fielding analytics endpoint if blueprint fails"""
    try:
        from services.analytics_service import AnalyticsService
        analytics = AnalyticsService.get_player_fielding_analytics(team_id)
        return jsonify(analytics), 200
    except Exception as e:
        return jsonify({"error": f"Failed to get player fielding analytics: {str(e)}"}), 500
```

### 3. Simplified Blueprint Registration in `api/__init__.py`

Replace the complex registration logic with a simpler approach:

```python
# Register analytics blueprint - simplified approach
try:
    # Import from the flat module (analytics.py)
    from api.analytics import analytics_bp
    
    # Register blueprint directly with proper URL prefix
    api.register_blueprint(analytics_bp, url_prefix='/analytics')
    print("Successfully registered analytics blueprint")
    
    # Check if any of the RESTful routes exist in the blueprint
    restful_routes = [rule for rule in analytics_bp.deferred_functions 
                     if 'get_team_analytics_restful' in str(rule) or 
                        'get_player_batting_analytics' in str(rule) or
                        'get_player_fielding_analytics' in str(rule)]
    
    if restful_routes:
        print(f"RESTful analytics routes are registered: {len(restful_routes)} found")
    else:
        print("WARNING: No RESTful analytics routes found in blueprint")
except Exception as e:
    print(f"Error registering analytics blueprint: {e}")
```

### 4. Enhanced `analytics.py` Endpoint Implementation

Make sure the RESTful endpoints are properly implemented in `analytics.py`:

```python
# RESTful endpoint for team analytics
@analytics_bp.route('/teams/<int:team_id>', methods=['GET'])
@jwt_required
def get_team_analytics_restful(team_id):
    """
    Get team analytics across all games using RESTful pattern.
    """
    print(f"RESTful team analytics endpoint called for team {team_id}")
    try:
        analytics = AnalyticsService.get_team_analytics(team_id)
        return jsonify(analytics), 200
    except Exception as e:
        return jsonify({"error": f"Failed to get team analytics: {str(e)}"}), 500

# RESTful endpoint for player batting analytics
@analytics_bp.route('/teams/<int:team_id>/players/batting', methods=['GET'])
@jwt_required
def get_player_batting_analytics(team_id):
    """
    Get batting analytics for all players in a team using RESTful pattern.
    """
    print(f"RESTful player batting analytics endpoint called for team {team_id}")
    try:
        analytics = AnalyticsService.get_player_batting_analytics(team_id)
        return jsonify(analytics), 200
    except Exception as e:
        return jsonify({"error": f"Failed to get player batting analytics: {str(e)}"}), 500

# RESTful endpoint for player fielding analytics
@analytics_bp.route('/teams/<int:team_id>/players/fielding', methods=['GET'])
@jwt_required
def get_player_fielding_analytics(team_id):
    """
    Get fielding analytics for all players in a team using RESTful pattern.
    """
    print(f"RESTful player fielding analytics endpoint called for team {team_id}")
    try:
        analytics = AnalyticsService.get_player_fielding_analytics(team_id)
        return jsonify(analytics), 200
    except Exception as e:
        return jsonify({"error": f"Failed to get player fielding analytics: {str(e)}"}), 500
```

### 5. Flask Debug Configuration

Ensure that debug logging is enabled for Flask to better understand registration issues:

```python
# Add to app.py near the top
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
```

## Deployment Instructions

1. Make the changes outlined above
2. Run a local test to verify endpoint registrations
3. Deploy to Heroku
4. Run the verification script to confirm all endpoints are working:
   ```
   node testing/verify-restful-analytics.js
   ```

## Fallback Plan

If blueprint-based registration continues to fail after these changes, we have two options:

1. **Direct Route Registration**: Continue using the direct routes in app.py which should work regardless of blueprint issues
2. **Frontend Adaptation**: Update the frontend to conditionally fall back to legacy endpoints if RESTful endpoints fail

## Post-Deployment Tasks

After successful deployment:

1. Update the API documentation to reflect the standardized endpoints
2. Add the new endpoints to automated tests
3. Consider a more comprehensive API versioning strategy for future updates