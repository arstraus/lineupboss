# API Architecture Guide

## Blueprint Structure

This API uses a package-based blueprint architecture for modularity and maintainability.

### Structure Overview

```
/backend/api/
  ├── __init__.py             # Main api blueprint initialization
  ├── auth/                   # Auth as a package
  │   ├── __init__.py         # Exports auth_bp 
  │   └── routes.py           # Route definitions
  ├── teams/
  │   ├── __init__.py
  │   └── routes.py
  ...
```

### Standard Package Structure

Each feature module should follow this standard structure:

1. **__init__.py**: Creates the blueprint and imports routes
```python
from flask import Blueprint

# Create the blueprint
feature_bp = Blueprint('feature_name', __name__)

# Import routes to register them with the blueprint
from api.feature_name.routes import *
```

2. **routes.py**: Defines endpoints using the blueprint from __init__
```python
from api.feature_name import feature_bp
from flask import jsonify, request
from flask_jwt_extended import jwt_required

@feature_bp.route('/endpoint', methods=['GET'])
@jwt_required()
def get_something():
    # Implementation
    return jsonify({"result": "data"})
```

### Adding a New Feature Module

To add a new feature:

1. Create a new directory: `/backend/api/feature_name/`
2. Create `__init__.py` with:
   ```python
   from flask import Blueprint
   feature_bp = Blueprint('feature_name', __name__)
   from api.feature_name.routes import *
   ```
3. Create `routes.py` with:
   ```python
   from api.feature_name import feature_bp
   
   @feature_bp.route('/endpoint', methods=['GET'])
   def get_something():
       # Implementation
       pass
   ```
4. Register in main `api/__init__.py`:
   ```python
   try:
       from api.feature_name import feature_bp
       api.register_blueprint(feature_bp, url_prefix='/feature-name')
   except ImportError as e:
       print(f"ERROR: Could not import feature_name module: {e}")
   ```

### Blueprint Registration Patterns

There are two ways to register blueprints in the main API:

1. **Direct Registration**:
```python
try:
    from api.feature_name import feature_bp
    api.register_blueprint(feature_bp, url_prefix='/feature-name')
except Exception as e:
    print(f"Error registering feature_name blueprint: {e}")
```

2. **Helper Function** (for consistency):
```python
register_blueprint(api, 'feature_name', 'feature_bp', '/feature-name')
```

### Best Practices

- Keep routes specific to their domain
- Use route parameters for resource identification
- Follow RESTful naming conventions
- Include proper error handling using standardize_error_response
- Document with docstrings and update API_ENDPOINTS.md
- Use the blueprint defined in `__init__.py` in your routes
- Avoid duplicate route definitions
- Include a README.md in each package explaining its purpose

### Nested Blueprints

For cases where you need nested URLs (e.g., `/teams/{team_id}/players`), create a nested blueprint:

```python
# In /api/players/__init__.py
players_nested = Blueprint('players_nested', __name__)

# Then register it with different URL prefix:
api.register_blueprint(players_nested, url_prefix='/teams')
```

### Error Handling Pattern

Use the standardized error handling pattern:
```python
@feature_bp.route('/endpoint', methods=['GET'])
@jwt_required()
def get_something():
    try:
        # Implementation
        return jsonify({"result": "data"})
    except Exception as e:
        # Use standardized error response
        from backend.utils import standardize_error_response
        return standardize_error_response(e, "Failed to get data")
```