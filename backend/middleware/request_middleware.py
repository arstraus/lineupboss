"""
Request processing middleware for LineupBoss API.

This module provides request processing middleware components
to handle common request/response processing tasks.
"""

import time
import uuid
from functools import wraps
from flask import g, request, current_app

class RequestMiddleware:
    """Request processing middleware for handling request/response."""
    
    @staticmethod
    def log_request(f):
        """
        Middleware to log request details.
        
        This middleware logs the request method, path, and duration.
        
        Returns:
            Function that logs the request and calls the original function
        """
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Generate a request ID
            request_id = str(uuid.uuid4())
            g.request_id = request_id
            
            # Get the start time
            start_time = time.time()
            
            # Log the request
            current_app.logger.info(
                f"Request {request_id}: {request.method} {request.path} - Started"
            )
            
            # Call the original function and capture the response
            response = f(*args, **kwargs)
            
            # Calculate the duration
            duration = time.time() - start_time
            
            # Log the response
            current_app.logger.info(
                f"Request {request_id}: {request.method} {request.path} - "
                f"Completed in {duration:.4f}s with status {response.status_code}"
            )
            
            return response
        
        return decorated_function
    
    @staticmethod
    def rate_limit(requests_per_minute=60):
        """
        Middleware to apply rate limiting to routes.
        
        This middleware limits the number of requests a user can make per minute.
        
        Args:
            requests_per_minute: Maximum number of requests allowed per minute
            
        Returns:
            Function that applies rate limiting and calls the original function
        """
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                # Get the user ID from the request
                from flask_jwt_extended import get_jwt_identity
                
                user_id = get_jwt_identity()
                
                # Apply rate limiting based on user ID
                # This is a simplified implementation
                # In a real-world scenario, you would use Redis or a similar solution
                # to track request counts across multiple instances
                
                # For now, just log a warning if we detect excessive requests
                from flask import g
                if hasattr(g, 'request_count') and g.request_count > requests_per_minute:
                    current_app.logger.warning(
                        f"Rate limit exceeded for user {user_id}: "
                        f"{g.request_count} requests/minute"
                    )
                
                # Call the original function
                return f(*args, **kwargs)
            
            return decorated_function
        
        return decorator
    
    @staticmethod
    def validate_json(schema=None):
        """
        Middleware to validate JSON request body against a schema.
        
        This middleware validates the request JSON body against a schema
        and returns an error response if validation fails.
        
        Args:
            schema: JSON schema to validate against (optional)
            
        Returns:
            Function that validates the request and calls the original function
        """
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                from backend.utils import standardize_error_response
                
                # Check if the request has a JSON body
                if not request.is_json:
                    return standardize_error_response(
                        'Request must be JSON', 
                        400
                    )
                
                # Get the JSON body
                data = request.get_json()
                
                # If schema is provided, validate against it
                if schema:
                    import jsonschema
                    
                    try:
                        jsonschema.validate(data, schema)
                    except jsonschema.exceptions.ValidationError as e:
                        return standardize_error_response(
                            'Invalid request data',
                            400,
                            str(e)
                        )
                
                # Call the original function
                return f(*args, **kwargs)
            
            return decorated_function
        
        return decorator
    
    @staticmethod
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
        from middleware.auth_middleware import AuthMiddleware
        
        current_headers = dict(request.headers)
        
        # Get the auth header
        auth_header = AuthMiddleware.get_auth_header()
        
        # Add it to the headers if it exists
        if auth_header:
            from werkzeug.datastructures import Headers
            headers = Headers(current_headers)
            headers['Authorization'] = auth_header
            current_headers = headers
        
        # Save the original headers
        original_headers = request.headers
        
        try:
            # Update request headers with forwarded headers
            request.headers = current_headers
            
            # Call the function
            return function(*args, **kwargs)
        finally:
            # Restore original headers
            request.headers = original_headers