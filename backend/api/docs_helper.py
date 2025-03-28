"""
Helper module for documenting API endpoints using the OpenAPI specification.

This module provides utility functions to simplify the documentation of API endpoints
using the OpenAPI/Swagger specification. It's designed to be imported by route modules
to document their endpoints.
"""

# Import the create_endpoint_spec function from the docs module
try:
    from api.docs import create_endpoint_spec
except ImportError:
    # If the docs module is not available, provide a dummy function
    def create_endpoint_spec(*args, **kwargs):
        pass

def document_endpoint(blueprint, path, methods, summary, description=None, params=None, 
                    request_body=None, responses=None, security=None):
    """
    Document an API endpoint using the OpenAPI specification.
    
    This is a wrapper around create_endpoint_spec that handles import errors
    and provides sensible defaults.
    
    Args:
        blueprint: The Flask blueprint the route belongs to
        path: The path of the endpoint (with {param} style parameters)
        methods: List of HTTP methods supported by the endpoint
        summary: A short summary of the endpoint
        description: A longer description of the endpoint
        params: List of parameters for the endpoint
        request_body: Description of the request body
        responses: Dictionary of possible responses
        security: Security requirements for the endpoint
    """
    try:
        create_endpoint_spec(
            blueprint=blueprint,
            path=path,
            methods=methods,
            summary=summary,
            description=description,
            params=params,
            request_body=request_body,
            responses=responses
        )
    except Exception as e:
        # Optional documentation - silently continue if there's an error
        print(f"WARNING: Failed to document endpoint {path}: {e}")
        pass

# Reusable response schemas
AUTH_401_RESPONSE = {
    'description': 'Unauthorized - Authentication required',
    'content': {
        'application/json': {
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {
                        'type': 'string',
                        'example': 'Missing or invalid authorization token'
                    }
                }
            }
        }
    }
}

NOT_FOUND_404_RESPONSE = {
    'description': 'Resource not found',
    'content': {
        'application/json': {
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {
                        'type': 'string',
                        'example': 'Resource not found'
                    }
                }
            }
        }
    }
}

BAD_REQUEST_400_RESPONSE = {
    'description': 'Bad request - Invalid input data',
    'content': {
        'application/json': {
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {
                        'type': 'string',
                        'example': 'Invalid input data'
                    }
                }
            }
        }
    }
}

FORBIDDEN_403_RESPONSE = {
    'description': 'Forbidden - Insufficient permissions',
    'content': {
        'application/json': {
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {
                        'type': 'string',
                        'example': 'Insufficient permissions to access this resource'
                    }
                }
            }
        }
    }
}

SERVER_ERROR_500_RESPONSE = {
    'description': 'Server error',
    'content': {
        'application/json': {
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {
                        'type': 'string',
                        'example': 'An unexpected error occurred'
                    }
                }
            }
        }
    }
}

# Reusable parameter templates
TEAM_ID_PARAM = {
    'name': 'team_id',
    'in': 'path',
    'required': True,
    'schema': {
        'type': 'integer'
    },
    'description': 'The ID of the team'
}

PLAYER_ID_PARAM = {
    'name': 'player_id',
    'in': 'path',
    'required': True,
    'schema': {
        'type': 'integer'
    },
    'description': 'The ID of the player'
}

GAME_ID_PARAM = {
    'name': 'game_id',
    'in': 'path',
    'required': True,
    'schema': {
        'type': 'integer'
    },
    'description': 'The ID of the game'
}

# Common schema components
TEAM_SCHEMA = {
    'type': 'object',
    'properties': {
        'id': {
            'type': 'integer',
            'example': 1
        },
        'name': {
            'type': 'string',
            'example': 'Tigers'
        },
        'league': {
            'type': 'string',
            'example': 'Little League'
        },
        'user_id': {
            'type': 'integer',
            'example': 1
        },
        'created_at': {
            'type': 'string',
            'format': 'date-time',
            'example': '2023-01-01T00:00:00Z'
        }
    }
}

PLAYER_SCHEMA = {
    'type': 'object',
    'properties': {
        'id': {
            'type': 'integer',
            'example': 1
        },
        'name': {
            'type': 'string',
            'example': 'John Smith'
        },
        'team_id': {
            'type': 'integer',
            'example': 1
        },
        'position': {
            'type': 'string',
            'example': 'Pitcher'
        },
        'batting_order': {
            'type': 'integer',
            'example': 1
        },
        'created_at': {
            'type': 'string',
            'format': 'date-time',
            'example': '2023-01-01T00:00:00Z'
        }
    }
}

GAME_SCHEMA = {
    'type': 'object',
    'properties': {
        'id': {
            'type': 'integer',
            'example': 1
        },
        'team_id': {
            'type': 'integer',
            'example': 1
        },
        'opponent': {
            'type': 'string',
            'example': 'Lions'
        },
        'game_date': {
            'type': 'string',
            'format': 'date-time',
            'example': '2023-01-01T15:00:00Z'
        },
        'location': {
            'type': 'string',
            'example': 'Home field'
        },
        'created_at': {
            'type': 'string',
            'format': 'date-time',
            'example': '2023-01-01T00:00:00Z'
        }
    }
}

def get_standard_responses(include_auth=True, include_not_found=True, include_bad_request=True):
    """
    Get a dictionary of standard responses for API endpoints.
    
    Args:
        include_auth: Whether to include the 401 Unauthorized response
        include_not_found: Whether to include the 404 Not Found response
        include_bad_request: Whether to include the 400 Bad Request response
        
    Returns:
        Dictionary of standard responses
    """
    responses = {
        '500': SERVER_ERROR_500_RESPONSE
    }
    
    if include_auth:
        responses['401'] = AUTH_401_RESPONSE
        
    if include_not_found:
        responses['404'] = NOT_FOUND_404_RESPONSE
        
    if include_bad_request:
        responses['400'] = BAD_REQUEST_400_RESPONSE
        
    return responses