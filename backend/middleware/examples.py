"""
Example usage of middleware components.

This module provides examples of how to use the middleware components
in route definitions. These examples are not meant to be used in production,
but rather as a reference for developers.
"""

from flask import Blueprint, jsonify
from middleware.auth_middleware import AuthMiddleware
from middleware.feature_middleware import FeatureMiddleware
from middleware.request_middleware import RequestMiddleware

examples = Blueprint('examples', __name__, url_prefix='/examples')

# Example of using the authenticate middleware
@examples.route('/auth', methods=['GET'])
@AuthMiddleware.authenticate
def example_auth():
    """Example route showing authentication middleware usage."""
    from flask import g
    
    return jsonify({
        'message': 'Authentication successful',
        'user_id': g.user_id
    })

# Example of using the admin_required middleware
@examples.route('/admin', methods=['GET'])
@AuthMiddleware.admin_required
def example_admin():
    """Example route showing admin_required middleware usage."""
    from flask import g
    
    return jsonify({
        'message': 'Admin access successful',
        'user_id': g.user_id,
        'user_role': g.user.role
    })

# Example of using the feature_required middleware
@examples.route('/feature', methods=['GET'])
@FeatureMiddleware.feature_required('ai_lineup_generation')
def example_feature():
    """Example route showing feature_required middleware usage."""
    from flask import g
    
    return jsonify({
        'message': 'Feature access successful',
        'user_id': g.user_id,
        'feature': 'ai_lineup_generation'
    })

# Example of using the log_request middleware
@examples.route('/log', methods=['GET'])
@RequestMiddleware.log_request
def example_log():
    """Example route showing log_request middleware usage."""
    return jsonify({
        'message': 'Request logged successfully'
    })

# Example of using the rate_limit middleware
@examples.route('/rate-limit', methods=['GET'])
@AuthMiddleware.authenticate
@RequestMiddleware.rate_limit(requests_per_minute=10)
def example_rate_limit():
    """Example route showing rate_limit middleware usage."""
    return jsonify({
        'message': 'Rate limit check passed'
    })

# Example of using the validate_json middleware
@examples.route('/validate', methods=['POST'])
@RequestMiddleware.validate_json({
    'type': 'object',
    'properties': {
        'name': {'type': 'string'},
        'age': {'type': 'number', 'minimum': 0}
    },
    'required': ['name', 'age']
})
def example_validate():
    """Example route showing validate_json middleware usage."""
    from flask import request
    
    data = request.get_json()
    
    return jsonify({
        'message': 'Validation successful',
        'data': data
    })

# Example of using multiple middleware components together
@examples.route('/combined', methods=['GET'])
@RequestMiddleware.log_request
@AuthMiddleware.authenticate
@FeatureMiddleware.feature_required('analytics')
def example_combined():
    """Example route showing multiple middleware components together."""
    from flask import g
    
    return jsonify({
        'message': 'All middleware checks passed',
        'user_id': g.user_id,
        'feature': 'analytics'
    })

# Example of using resource ownership validation
@examples.route('/resource/<string:resource_type>/<int:resource_id>', methods=['GET'])
@AuthMiddleware.authenticate
def example_resource_ownership(resource_type, resource_id):
    """Example route showing resource ownership validation."""
    from flask import g
    
    # Validate resource ownership
    resource, error_response = AuthMiddleware.validate_user_owns_resource(
        resource_type,
        resource_id,
        g.user_id
    )
    
    if error_response:
        return error_response
    
    return jsonify({
        'message': 'Resource ownership validated',
        'resource_type': resource_type,
        'resource_id': resource_id,
        'resource': str(resource)
    })

# Example of using team limit check
@examples.route('/team-limit', methods=['GET'])
@AuthMiddleware.authenticate
def example_team_limit():
    """Example route showing team limit check."""
    from flask import g
    
    # Check team limit
    has_capacity, error_response, team_count, team_limit = FeatureMiddleware.check_team_limit(
        user_id=g.user_id
    )
    
    if not has_capacity:
        return error_response
    
    return jsonify({
        'message': 'Team limit check passed',
        'team_count': team_count,
        'team_limit': team_limit,
        'remaining': team_limit - team_count
    })