"""
API documentation module using Swagger/OpenAPI.
This is a fallback version that doesn't use any external dependencies.
"""
from flask import Blueprint, jsonify, render_template_string

# Create a Blueprint for docs
docs = Blueprint('docs', __name__)

# Create a dummy swagger UI blueprint to avoid import errors
swagger_ui_blueprint = Blueprint('swagger_ui', __name__)

# Basic HTML template for API documentation
API_DOCS_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Lineup API Documentation</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #333; }
        h2 { color: #666; border-bottom: 1px solid #ddd; padding-bottom: 10px; }
        .endpoint { margin-bottom: 20px; padding: 10px; background-color: #f8f8f8; border-radius: 5px; }
        .method { font-weight: bold; color: #0066cc; }
        .path { font-family: monospace; }
        .description { margin-top: 5px; }
    </style>
</head>
<body>
    <h1>Lineup API Documentation</h1>
    <p>This is a simplified API documentation page as the full Swagger UI is unavailable.</p>
    
    <h2>Authentication</h2>
    <div class="endpoint">
        <div><span class="method">POST</span> <span class="path">/api/auth/register</span></div>
        <div class="description">Register a new user with email and password</div>
    </div>
    <div class="endpoint">
        <div><span class="method">POST</span> <span class="path">/api/auth/login</span></div>
        <div class="description">Log in a user with email and password</div>
    </div>
    <div class="endpoint">
        <div><span class="method">GET</span> <span class="path">/api/auth/me</span></div>
        <div class="description">Get current user information</div>
    </div>
    
    <h2>Teams</h2>
    <div class="endpoint">
        <div><span class="method">GET</span> <span class="path">/api/teams</span></div>
        <div class="description">Get all teams for the current user</div>
    </div>
    <div class="endpoint">
        <div><span class="method">POST</span> <span class="path">/api/teams</span></div>
        <div class="description">Create a new team</div>
    </div>
    <div class="endpoint">
        <div><span class="method">GET</span> <span class="path">/api/teams/{team_id}</span></div>
        <div class="description">Get a specific team</div>
    </div>
    <div class="endpoint">
        <div><span class="method">PUT</span> <span class="path">/api/teams/{team_id}</span></div>
        <div class="description">Update a team</div>
    </div>
    <div class="endpoint">
        <div><span class="method">DELETE</span> <span class="path">/api/teams/{team_id}</span></div>
        <div class="description">Delete a team</div>
    </div>
    
    <h2>Players</h2>
    <div class="endpoint">
        <div><span class="method">GET</span> <span class="path">/api/players/team/{team_id}</span></div>
        <div class="description">Get all players for a team</div>
    </div>
    <div class="endpoint">
        <div><span class="method">POST</span> <span class="path">/api/players/team/{team_id}</span></div>
        <div class="description">Create a new player</div>
    </div>
    
    <h2>Games</h2>
    <div class="endpoint">
        <div><span class="method">GET</span> <span class="path">/api/games/team/{team_id}</span></div>
        <div class="description">Get all games for a team</div>
    </div>
</body>
</html>
"""

@docs.route('/')
def docs_index():
    return render_template_string(API_DOCS_HTML)

@docs.route('/swagger.json')
def swagger_json():
    """Basic OpenAPI spec"""
    openapi_spec = {
        "openapi": "3.0.2",
        "info": {
            "title": "Lineup API",
            "version": "1.0.0",
            "description": "API for baseball lineup management"
        },
        "paths": {}
    }
    return jsonify(openapi_spec)