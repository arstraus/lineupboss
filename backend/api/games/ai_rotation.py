"""
AI fielding rotation module using the new pattern for feature-gated endpoints.

This module demonstrates the recommended approach for implementing
feature-gated functionality in a standardized way.
"""

from flask import Blueprint, request, jsonify, g
from shared.database import db_session
from utils import token_required, standardize_error_response
from services.ai_service import AIService
from services.game_service import GameService
from shared.models import User
from shared.subscription_tiers import has_feature

# Create a blueprint for AI-specific endpoints
ai_rotation_bp = Blueprint('ai_rotation', __name__)

@ai_rotation_bp.route('/games/<int:game_id>/ai-fielding-rotation', methods=['POST'])
@token_required
def generate_ai_fielding_rotation(game_id):
    """
    Generate AI-based fielding rotation for a specific game.
    
    This endpoint demonstrates the recommended approach for feature gating:
    1. Use @token_required for authentication
    2. Check feature access inside the function
    3. Return standardized error responses
    
    Args:
        game_id: Game ID
        
    Returns:
        AI-generated fielding rotation
    """
    user_id = g.user_id
    
    try:
        # Parse request data
        data = request.get_json()
        
        # Validate request data
        if not data or not isinstance(data.get('players'), list) or len(data.get('players', [])) == 0:
            return standardize_error_response(
                'Player data is required for AI rotation generation',
                400
            )
        
        # Check if user has the AI lineup generation feature
        with db_session(read_only=True) as session:
            user = session.query(User).filter(User.id == user_id).first()
            
            if not user:
                return standardize_error_response(
                    'User not found',
                    404
                )
            
            # Skip feature check for admins
            if user.role != 'admin':
                if not has_feature(user.subscription_tier, 'ai_lineup_generation'):
                    return standardize_error_response(
                        'Subscription required',
                        403,
                        {
                            'message': 'This feature requires a Pro subscription',
                            'current_tier': user.subscription_tier,
                            'required_feature': 'ai_lineup_generation',
                            'upgrade_url': '/account/billing'
                        }
                    )
            
            # Verify game belongs to user
            game = GameService.get_game(session, game_id, user_id)
            if not game:
                return standardize_error_response(
                    'Game not found or unauthorized',
                    404
                )
            
            # Get required parameters from request data
            players = data['players']
            innings = data.get('innings', game.innings) or 6  # Default to game innings or fallback to 6
            required_positions = data.get('required_positions', [])
            infield_positions = data.get('infield_positions', [])
            outfield_positions = data.get('outfield_positions', [])
            
            # Get customization options with defaults
            options = data.get('options', {})
            no_consecutive_innings = options.get('noConsecutiveInnings', True)
            balance_playing_time = options.get('balancePlayingTime', True)
            allow_same_position = options.get('allowSamePositionMultipleTimes', False)
            strict_position_balance = options.get('strictPositionBalance', True)
            temperature = options.get('temperature', 0.7)
            
            try:
                # Call AI service to generate rotation
                rotation_result = AIService.generate_fielding_rotation(
                    game_id, 
                    players, 
                    innings,
                    required_positions,
                    infield_positions,
                    outfield_positions,
                    no_consecutive_innings,
                    balance_playing_time,
                    allow_same_position,
                    strict_position_balance,
                    temperature
                )
                
                return jsonify(rotation_result), 200
            except ValueError as ve:
                if "timeout" in str(ve).lower():
                    # If timeout occurs, return an informative message
                    return standardize_error_response(
                        'AI Rotation Timeout',
                        202,  # Accepted but not completed
                        {
                            'message': 'The AI fielding rotation could not be generated in time. Please try again later or create a manual rotation.',
                            'error': str(ve),
                            'success': False
                        }
                    )
                else:
                    # Other value errors should be passed through
                    raise ve
    except ValueError as e:
        return standardize_error_response(
            'Invalid request data',
            400,
            str(e)
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return standardize_error_response(
            'Error processing request',
            500,
            str(e)
        )