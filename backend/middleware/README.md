# LineupBoss Middleware

This directory contains middleware components for the LineupBoss API. These middleware components provide common functionality such as authentication, feature gating, and request/response processing.

## Available Middleware

### AuthMiddleware

The `AuthMiddleware` class provides authentication-related middleware components.

#### Methods

- `authenticate`: Middleware to verify JWT token and set user_id in Flask g object
- `admin_required`: Middleware to verify the user has admin role
- `get_auth_header`: Get the Authorization header from various sources
- `validate_user_owns_resource`: Validate that a user owns a resource

#### Usage Examples

```python
from middleware.auth_middleware import AuthMiddleware

# Example of using the authenticate middleware
@app.route('/api/resource', methods=['GET'])
@AuthMiddleware.authenticate
def get_resource():
    from flask import g
    user_id = g.user_id
    # ...

# Example of using the admin_required middleware
@app.route('/api/admin/users', methods=['GET'])
@AuthMiddleware.admin_required
def get_users():
    # Only admin users can access this route
    # ...

# Example of validating resource ownership
@app.route('/api/teams/<int:team_id>', methods=['DELETE'])
@AuthMiddleware.authenticate
def delete_team(team_id):
    from flask import g
    
    # Validate resource ownership
    team, error_response = AuthMiddleware.validate_user_owns_resource(
        'team',
        team_id,
        g.user_id
    )
    
    if error_response:
        return error_response
    
    # Delete the team
    # ...
```

### FeatureMiddleware

The `FeatureMiddleware` class provides feature gating middleware components.

#### Methods

- `check_feature`: Check if a user has access to a feature
- `feature_required`: Middleware to restrict routes based on features available in subscription tier
- `check_team_limit`: Check if a user has reached their team limit

#### Usage Examples

```python
from middleware.feature_middleware import FeatureMiddleware

# Example of using the feature_required middleware
@app.route('/api/games/<int:game_id>/ai-fielding-rotation', methods=['POST'])
@FeatureMiddleware.feature_required('ai_lineup_generation')
def generate_ai_fielding_rotation(game_id):
    # Only users with access to the ai_lineup_generation feature can access this route
    # ...

# Example of checking feature access in a route
@app.route('/api/teams/<int:team_id>/analytics', methods=['GET'])
@AuthMiddleware.authenticate
def get_team_analytics(team_id):
    from flask import g
    
    # Check feature access
    has_access, error_response = FeatureMiddleware.check_feature(
        'analytics', 
        user_id=g.user_id
    )
    
    if not has_access:
        return error_response
    
    # Get analytics data
    # ...

# Example of checking team limit
@app.route('/api/teams', methods=['POST'])
@AuthMiddleware.authenticate
def create_team():
    from flask import g, request
    
    # Check team limit
    has_capacity, error_response, team_count, team_limit = FeatureMiddleware.check_team_limit(
        user_id=g.user_id
    )
    
    if not has_capacity:
        return error_response
    
    # Create the team
    # ...
```

### RequestMiddleware

The `RequestMiddleware` class provides request processing middleware components.

#### Methods

- `log_request`: Middleware to log request details
- `rate_limit`: Middleware to apply rate limiting to routes
- `validate_json`: Middleware to validate JSON request body against a schema
- `direct_function_call`: Call a function directly while preserving request context

#### Usage Examples

```python
from middleware.request_middleware import RequestMiddleware

# Example of using the log_request middleware
@app.route('/api/resource', methods=['GET'])
@RequestMiddleware.log_request
def get_resource():
    # This request will be logged
    # ...

# Example of using the rate_limit middleware
@app.route('/api/resource', methods=['GET'])
@RequestMiddleware.rate_limit(requests_per_minute=10)
def get_resource():
    # This route is rate limited to 10 requests per minute
    # ...

# Example of using the validate_json middleware
@app.route('/api/resource', methods=['POST'])
@RequestMiddleware.validate_json({
    'type': 'object',
    'properties': {
        'name': {'type': 'string'},
        'age': {'type': 'number', 'minimum': 0}
    },
    'required': ['name', 'age']
})
def create_resource():
    # Request body will be validated against the schema
    # ...

# Example of using direct_function_call
@app.route('/api/proxy/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy(path):
    # Determine which function to call based on path
    if path == 'resource':
        return RequestMiddleware.direct_function_call(get_resource)
    # ...
```

## Combining Middleware

You can combine multiple middleware components to create a chain of middleware for a route.

```python
@app.route('/api/resource', methods=['POST'])
@RequestMiddleware.log_request
@AuthMiddleware.authenticate
@FeatureMiddleware.feature_required('feature_name')
@RequestMiddleware.validate_json(schema)
def create_resource():
    # This route is protected by multiple middleware components
    # ...
```

Note that the order of middleware matters. The middleware components are executed from bottom to top, meaning the innermost decorator is executed first, and the outermost decorator is executed last.

## Using in Blueprint Registration

You can apply middleware to all routes in a blueprint when registering it:

```python
from flask import Blueprint
from middleware.auth_middleware import AuthMiddleware

# Create a blueprint
my_blueprint = Blueprint('my_blueprint', __name__, url_prefix='/api/my-resource')

# Apply middleware to all routes in the blueprint
@my_blueprint.before_request
@AuthMiddleware.authenticate
def authenticate_request():
    pass

# Register routes on the blueprint
@my_blueprint.route('/', methods=['GET'])
def get_resources():
    # This route is protected by authenticate middleware
    # ...

# Register the blueprint with the app
app.register_blueprint(my_blueprint)
```

## Example Implementation

For reference, see `examples.py` in this directory for example usage of all middleware components.