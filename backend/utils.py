"""
Utility functions for the backend.
"""
import json
import re
from functools import wraps
from flask import jsonify, g, request
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity

# Legacy feature gating decorators
# Note: These decorators have been deprecated in favor of in-route feature checks.
# They are kept here for reference but are no longer used in the application.
#
# def subscription_required(required_tier):
#     """
#     [DEPRECATED] Decorator to restrict routes based on subscription tier.
#     This has been replaced by in-route feature checks.
#     """
#     pass
#
# def feature_required(feature_name):
#     """
#     [DEPRECATED] Decorator to restrict routes based on features available in subscription tier.
#     This has been replaced by in-route feature checks.
#     """
#     pass
#
# def team_limit_check(f):
#     """
#     [DEPRECATED] Decorator to check if a user has reached their team limit.
#     This has been replaced by in-route checks.
#     """
#     pass

# JWT helper functions - for standardized JWT usage

def token_required(f):
    """
    Decorator that combines jwt_required with setting g.user_id.
    
    This is a convenience wrapper around jwt_required that also
    sets g.user_id for use in the route function.
    
    Returns:
        Function that verifies the JWT token and sets g.user_id
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Verify the JWT token
            verify_jwt_in_request()
            
            # Get the user ID from the token
            user_id = get_jwt_identity()
            
            # Convert to int if it's a string
            if isinstance(user_id, str):
                user_id = int(user_id)
                
            # Store user_id in g for use in the route function
            g.user_id = user_id
            
            # Call the original function
            return f(*args, **kwargs)
        except Exception as e:
            print(f"Error in token_required decorator: {str(e)}")
            return jsonify({'error': 'Authentication error'}), 401
    
    return decorated_function

def extract_id_from_path(path, resource_type):
    """
    Extract an ID from a URL path for a specific resource type.
    
    Args:
        path: URL path
        resource_type: Resource type to find ID for (e.g., 'teams', 'games', 'players')
        
    Returns:
        ID if found, None otherwise
    """
    parts = path.split('/')
    for i, part in enumerate(parts):
        if part == resource_type and i+1 < len(parts) and parts[i+1].isdigit():
            return int(parts[i+1])
    return None

def get_auth_header():
    """
    Get the Authorization header from various sources.
    
    Tries multiple sources for the auth token in this order:
    1. Standard Authorization header
    2. Custom X-Authorization header
    3. JWT cookie
    4. token URL parameter
    
    Returns:
        Full authorization header string if found, None otherwise
    """
    # Try standard Authorization header
    auth_header = request.headers.get('Authorization')
    if auth_header:
        return auth_header
    
    # Try custom X-Authorization header
    x_auth = request.headers.get('X-Authorization')
    if x_auth:
        return x_auth
    
    # Try cookie
    jwt_cookie = request.cookies.get('jwt')
    if jwt_cookie:
        return f"Bearer {jwt_cookie}"
    
    # Try URL parameter
    token_param = request.args.get('token')
    if token_param:
        return f"Bearer {token_param}"
    
    return None

def forward_auth_header(headers_dict):
    """
    Add/forward the Authorization header to a headers dictionary.
    
    This function is useful when calling another function directly
    to ensure authentication headers are preserved.
    
    Args:
        headers_dict: Headers dictionary to modify
        
    Returns:
        Modified headers dictionary with Authorization header if available
    """
    auth_header = get_auth_header()
    if auth_header:
        from werkzeug.datastructures import Headers
        headers = Headers(headers_dict)
        headers['Authorization'] = auth_header
        return headers
    return headers_dict

def direct_function_call(function, *args, **kwargs):
    """
    Call a function directly while preserving request context.
    
    This function is especially useful for directly calling routes
    instead of redirecting to ensure headers and request data are preserved.
    
    Args:
        function: Function to call
        *args: Arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function
        
    Returns:
        Function's return value
    """
    # Forward authentication headers
    current_headers = dict(request.headers)
    forwarded_headers = forward_auth_header(current_headers)
    
    # Save the original headers
    original_headers = request.headers
    
    try:
        # Update request headers with forwarded headers
        request.headers = forwarded_headers
        
        # Call the function
        return function(*args, **kwargs)
    finally:
        # Restore original headers
        request.headers = original_headers

def standardize_error_response(error_message, status_code=400, details=None):
    """
    Generate a standardized error response.
    
    Args:
        error_message: Error message
        status_code: HTTP status code
        details: Additional details about the error
        
    Returns:
        JSONified error response and status code
    """
    response = {
        'error': error_message
    }
    
    if details:
        response['details'] = details
        
    return jsonify(response), status_code