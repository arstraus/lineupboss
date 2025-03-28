"""
API documentation module using Swagger/OpenAPI.
This module provides a comprehensive API documentation using Flask-Swagger-UI.
"""
from flask import Blueprint, jsonify, request, current_app
from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from apispec_webframeworks.flask import FlaskPlugin
from flask_swagger_ui import get_swaggerui_blueprint

# Create a Blueprint for docs
docs = Blueprint('docs', __name__)

# Create Swagger UI blueprint
SWAGGER_URL = '/api/docs'
API_URL = '/api/docs/swagger.json'

swagger_ui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "Lineup Boss API",
        'docExpansion': "list",
        'deepLinking': True,
        'defaultModelsExpandDepth': 1,
        'defaultModelExpandDepth': 1,
    }
)

def configure_swagger(app):
    """
    Configure Swagger for the application.
    
    Args:
        app: Flask application instance
    """
    # Register the Swagger UI blueprint
    app.register_blueprint(swagger_ui_blueprint)
    
    # Initialize spec with APISpec
    spec = APISpec(
        title="Lineup Boss API",
        version="1.0.0",
        openapi_version="3.0.2",
        info=dict(
            description="API for baseball lineup management",
            contact=dict(email="support@lineupboss.com")
        ),
        plugins=[FlaskPlugin(), MarshmallowPlugin()],
    )
    
    return spec

# Store the spec as a global variable
spec = None

def init_spec(app):
    """Initialize the API spec with the application."""
    global spec
    spec = configure_swagger(app)
    
    # Add basic security schemes
    spec.components.security_scheme('BearerAuth', {
        'type': 'http',
        'scheme': 'bearer',
        'bearerFormat': 'JWT',
        'description': 'Enter JWT token in the format: Bearer <token>'
    })
    
    # Add routes to spec
    with app.test_request_context():
        # Include all blueprints with patterns
        _add_blueprint_routes(app, spec)

def _add_blueprint_routes(app, spec):
    """Add routes from blueprints to spec."""
    # This can be expanded as needed with more specific endpoint documentation
    # For now, we'll do minimal path registration
    for rule in app.url_map.iter_rules():
        if rule.endpoint != 'static' and not rule.rule.startswith('/api/docs'):
            path = rule.rule.replace('<', '{').replace('>', '}')
            methods = {}
            
            for method in rule.methods:
                if method not in ['HEAD', 'OPTIONS']:
                    methods[method.lower()] = {
                        'summary': f"{method} {path}",
                        'description': f"Endpoint for {method} {path}",
                        'responses': {
                            '200': {
                                'description': 'Success',
                                'content': {
                                    'application/json': {}
                                }
                            },
                            '400': {
                                'description': 'Bad Request',
                                'content': {
                                    'application/json': {}
                                }
                            },
                            '401': {
                                'description': 'Unauthorized',
                                'content': {
                                    'application/json': {}
                                }
                            },
                            '404': {
                                'description': 'Not Found',
                                'content': {
                                    'application/json': {}
                                }
                            }
                        }
                    }
                    
                    # Add security requirement for authenticated routes
                    if 'auth' in rule.endpoint or not path.startswith('/api/auth/'):
                        methods[method.lower()]['security'] = [{'BearerAuth': []}]
            
            if methods:
                spec.path(path=path, operations=methods)

@docs.route('/swagger.json')
def swagger_json():
    """Get the OpenAPI specification for the API."""
    global spec
    if spec is None:
        # Fallback if spec hasn't been initialized
        return jsonify({
            "openapi": "3.0.2",
            "info": {
                "title": "Lineup API",
                "version": "1.0.0",
                "description": "API for baseball lineup management (loading...)"
            },
            "paths": {}
        })
    
    return jsonify(spec.to_dict())

# Create a partial API blueprint specification
def create_endpoint_spec(blueprint, path, methods, summary, description=None, params=None, request_body=None, responses=None):
    """
    Helper function to create an endpoint specification for the OpenAPI documentation.
    This can be used to document specific endpoints in more detail.
    
    Args:
        blueprint: The Flask blueprint the route belongs to
        path: The path of the endpoint (with {param} style parameters)
        methods: List of HTTP methods supported by the endpoint
        summary: A short summary of the endpoint
        description: A longer description of the endpoint
        params: List of parameters for the endpoint
        request_body: Description of the request body
        responses: Dictionary of possible responses
    """
    if spec is None:
        return
    
    if description is None:
        description = summary
    
    if params is None:
        params = []
    
    if responses is None:
        responses = {
            '200': {
                'description': 'Success',
                'content': {
                    'application/json': {}
                }
            },
            '400': {
                'description': 'Bad Request',
                'content': {
                    'application/json': {}
                }
            },
            '401': {
                'description': 'Unauthorized',
                'content': {
                    'application/json': {}
                }
            }
        }
    
    operations = {}
    for method in methods:
        method = method.lower()
        operations[method] = {
            'summary': summary,
            'description': description,
            'parameters': params,
            'responses': responses
        }
        
        if 'auth' in blueprint.name or blueprint.name != 'auth':
            operations[method]['security'] = [{'BearerAuth': []}]
        
        if request_body and method in ['post', 'put', 'patch']:
            operations[method]['requestBody'] = request_body
    
    if blueprint.url_prefix:
        full_path = blueprint.url_prefix + path
    else:
        full_path = path
    
    full_path = full_path.replace('<', '{').replace('>', '}')
    spec.path(path=full_path, operations=operations)