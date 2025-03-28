
"""
API Blueprint Registration

This module registers all API blueprints with the main API blueprint.
All routes should be defined in the respective blueprint modules and
registered here with the appropriate URL prefix.

- /api/system/... - System-wide endpoints
- /api/auth/... - Authentication endpoints
- /api/user/... - User profile endpoints
- /api/teams/... - Team management
- /api/players/... - Player management
- /api/games/... - Game management
- /api/admin/... - Admin functions
- /api/analytics/... - Analytics endpoints

Routes defined directly in app.py are deprecated and will be removed in a future release.
"""
from flask import Blueprint
import importlib
import traceback

# Main API blueprint with /api prefix
api = Blueprint('api', __name__, url_prefix='/api')

# Helper function to register a blueprint
def register_blueprint(parent, module_name, blueprint_name, url_prefix):
    """Register a blueprint with error handling and logging."""
    try:
        module = importlib.import_module(f'api.{module_name}')
        blueprint = getattr(module, blueprint_name)
        parent.register_blueprint(blueprint, url_prefix=url_prefix)
        print(f"Registered {module_name} blueprint with URL prefix {url_prefix}")
        return True
    except ImportError as e:
        print(f"Could not import {module_name} module: {e}")
        return False
    except AttributeError as e:
        print(f"Could not find blueprint {blueprint_name} in {module_name} module: {e}")
        return False
    except Exception as e:
        print(f"Error registering {module_name} blueprint: {e}")
        return False

# Register system blueprint (for core API functionality)
register_blueprint(api, 'system', 'system', '/')

# Register auth blueprint (for authentication)
register_blueprint(api, 'auth', 'auth', '/auth')

# Register users blueprint (for user profile management)
register_blueprint(api, 'users', 'users_bp', '/user')

# Register teams blueprint (for team management)
register_blueprint(api, 'teams', 'teams', '/teams')

# Register players blueprint (for player management)
register_blueprint(api, 'players', 'players', '/players')

# Register games blueprint (for game management)
register_blueprint(api, 'games', 'games', '/games')

# Register players nested-route blueprint
try:
    from api.games import games_nested
    api.register_blueprint(games_nested, url_prefix='/teams')
    print("Registered games_nested blueprint with URL prefix /teams")
except Exception as e:
    print(f"Error registering games_nested blueprint: {e}")

# Register games nested-route blueprint
try:
    from api.players import players_nested
    api.register_blueprint(players_nested, url_prefix='/teams')
    print("Registered players_nested blueprint with URL prefix /teams")
except Exception as e:
    print(f"Error registering players_nested blueprint: {e}")

# Register admin blueprint (for admin functions)
register_blueprint(api, 'admin', 'admin', '/admin')

# Register analytics blueprint (for team and player analytics)
try:
    # Import from package structure (preferred)
    try:
        # First try to import from the package
        from api.analytics import analytics_bp
        
        # Register blueprint with proper URL prefix
        api.register_blueprint(analytics_bp, url_prefix='/analytics')
        print(f"SUCCESS: Registered analytics blueprint with URL prefix /analytics")
        
        analytics_registered = True
    except ImportError as e:
        print(f"WARNING: Could not import analytics package: {e}")
        analytics_registered = False
except Exception as e:
    print(f"ERROR: Error registering analytics blueprint: {e}")
    print(f"Stack trace: {traceback.format_exc()}")
    analytics_registered = False

# Try to import docs with special handling for apispec dependency
try:
    # First check if apispec is available
    spec_loader = importlib.util.find_spec('apispec')
    if spec_loader is not None:
        from api.docs import docs
        api.register_blueprint(docs, url_prefix='/docs')
        print("Registered docs blueprint with URL prefix /docs")
    else:
        print("apispec module not found, skipping docs module")
except ImportError as e:
    print(f"Could not import docs module: {e}")
