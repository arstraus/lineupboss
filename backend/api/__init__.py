
from flask import Blueprint
import importlib

api = Blueprint('api', __name__, url_prefix='/api')

# Try to import each module separately
try:
    from api.auth import auth
    api.register_blueprint(auth, url_prefix='/auth')
except ImportError as e:
    print(f"Could not import auth module: {e}")

try:
    from api.teams import teams
    api.register_blueprint(teams, url_prefix='/teams')
except ImportError as e:
    print(f"Could not import teams module: {e}")

try:
    from api.players import players
    api.register_blueprint(players, url_prefix='/players')
except ImportError as e:
    print(f"Could not import players module: {e}")

try:
    from api.games import games
    api.register_blueprint(games, url_prefix='/games')
except ImportError as e:
    print(f"Could not import games module: {e}")
    
try:
    from api.admin import admin
    api.register_blueprint(admin, url_prefix='/admin')
except ImportError as e:
    print(f"Could not import admin module: {e}")

# Try to import docs with special handling for apispec dependency
try:
    # First check if apispec is available
    spec_loader = importlib.util.find_spec('apispec')
    if spec_loader is not None:
        from api.docs import docs
        api.register_blueprint(docs, url_prefix='/docs')
    else:
        print("apispec module not found, skipping docs module")
except ImportError as e:
    print(f"Could not import docs module: {e}")
