"""
Backend Fix for Analytics Service

This file provides the necessary fixes for the analytics service to properly
handle batting order data and fix the read_only parameter issue.

Instructions:
1. Apply these changes to the corresponding files in your backend
2. Restart the backend service after making the changes
3. Test the analytics endpoints to verify the fixes
"""

# ============================================================================
# Fix 1: Update the analytics_service.py file to handle the correct batting order format
# ============================================================================
"""
File: /backend/services/analytics_service.py

Problem:
- The analytics service expects batting order data in a different format than what's being returned

Fix:
- Update the get_batting_analytics and get_team_analytics methods to handle the actual batting order format
- Add proper error handling and logging for batting order data
"""

# Add this import at the top of the file if not already present
import logging
from typing import Dict, List, Any, Optional

# Fix for the get_batting_analytics method - modify the section that processes batting orders
def get_batting_analytics(team_id: int) -> List[Dict[str, Any]]:
    """Get batting analytics for all players in a team."""
    try:
        # Use the existing db_session context manager
        with db_session(read_only=True) as session:
            # [Existing code to fetch team, players, games...]
            
            # Modified section for handling batting orders
            batting_orders = session.query(BattingOrder).filter(
                BattingOrder.game_id.in_([g.id for g in games])
            ).all()
            
            # Create a mapping of game to batting order
            game_to_batting = {}
            for order in batting_orders:
                # Handle both possible formats of batting order data
                if hasattr(order, 'order_data') and order.order_data:
                    # Check if order_data is a list (array of player IDs)
                    if isinstance(order.order_data, list):
                        game_to_batting[order.game_id] = order.order_data
                    # If it's a dict with an order_data field containing the array
                    elif isinstance(order.order_data, dict) and 'order_data' in order.order_data:
                        game_to_batting[order.game_id] = order.order_data['order_data']
            
            # Rest of the original method...
            # When accessing batting position:
            for player in team_players:
                # [Existing player processing code...]
                
                # Modified section for batting position handling
                for game in games:
                    if game.id in game_to_batting and player.id in game_to_batting[game.id]:
                        try:
                            # Get player's position in the batting order (1-based index)
                            position = game_to_batting[game.id].index(player.id) + 1
                            # [Rest of the existing code...]
                        except (ValueError, IndexError) as e:
                            logging.warning(f"Error processing batting position for player {player.id} in game {game.id}: {e}")
                            continue
            
            # Important: Add has_data flag to indicate if any player has batting data
            for player_stats in result:
                player_stats['has_data'] = (
                    player_stats.get('games_in_lineup', 0) > 0 and
                    bool(player_stats.get('batting_positions', {}))
                )
            
            return result
    except Exception as e:
        logging.error(f"Error in get_batting_analytics: {e}")
        # Return empty list with appropriate structure on error
        return []

# Fix for the get_team_analytics method
def get_team_analytics(team_id: int) -> Dict[str, Any]:
    """Get team analytics data."""
    try:
        with db_session(read_only=True) as session:
            # [Existing code to fetch team, games...]
            
            # Initialize result with default values
            result = {
                'total_games': 0,
                'games_by_month': {},
                'games_by_day': {
                    'Monday': 0, 'Tuesday': 0, 'Wednesday': 0, 'Thursday': 0,
                    'Friday': 0, 'Saturday': 0, 'Sunday': 0
                },
                'has_data': False  # Initialize has_data flag
            }
            
            # Get all games with dates
            games_with_dates = [g for g in games if g.date]
            
            # Check if there are any games with both batting orders and fielding rotations
            games_with_data = []
            for game in games_with_dates:
                has_batting = False
                has_fielding = False
                
                # Check for batting order
                batting_order = session.query(BattingOrder).filter_by(game_id=game.id).first()
                if batting_order and hasattr(batting_order, 'order_data') and batting_order.order_data:
                    # Handle both possible formats
                    if isinstance(batting_order.order_data, list) and batting_order.order_data:
                        has_batting = True
                    elif isinstance(batting_order.order_data, dict) and 'order_data' in batting_order.order_data:
                        has_batting = bool(batting_order.order_data['order_data'])
                
                # Check for fielding rotations
                fielding_rotations = session.query(FieldingRotation).filter_by(game_id=game.id).count()
                has_fielding = fielding_rotations > 0
                
                # Add to games with data if it has both
                if has_batting and has_fielding:
                    games_with_data.append(game)
            
            # Set has_data flag based on whether any valid games were found
            result['has_data'] = len(games_with_data) > 0
            
            # Only count games with both batting and fielding data
            if games_with_data:
                result['total_games'] = len(games_with_data)
                
                # Process games by month and day
                for game in games_with_data:
                    # [Existing code for month/day processing...]
            
            return result
    except Exception as e:
        logging.error(f"Error in get_team_analytics: {e}")
        # Return default structure with has_data=False on error
        return {
            'total_games': 0,
            'games_by_month': {},
            'games_by_day': {
                'Monday': 0, 'Tuesday': 0, 'Wednesday': 0, 'Thursday': 0,
                'Friday': 0, 'Saturday': 0, 'Sunday': 0
            },
            'has_data': False
        }

# ============================================================================
# Fix 2: Update the database access function to handle the read_only parameter
# ============================================================================
"""
File: /backend/shared/database.py

Problem:
- The get_db() function doesn't accept the read_only parameter
- The db_session context manager uses read_only but get_db() doesn't handle it

Fix:
- Update the get_db() function to accept and properly handle the read_only parameter
"""

# Update the get_db function to accept read_only parameter
def get_db(read_only=False):
    """
    Get database session.
    
    Args:
        read_only (bool): If True, sets the transaction to read-only mode.
    
    Returns:
        SQLAlchemy session
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker, scoped_session
    
    # Get the engine (assuming this part exists already)
    engine = create_engine(DATABASE_URL)
    
    # Create session factory
    session_factory = sessionmaker(bind=engine)
    Session = scoped_session(session_factory)
    
    # Create session
    session = Session()
    
    # Set read-only mode if requested
    if read_only:
        session.execute("SET TRANSACTION READ ONLY")
    
    return session

# ============================================================================
# Fix 3: Add a diagnostic endpoint to debug analytics data issues
# ============================================================================
"""
File: /backend/api/analytics/routes.py

Problem:
- Need a way to debug analytics data generation
- Current debug endpoint has errors

Fix:
- Add a proper diagnostic endpoint for analytics data
"""

# Add this to the analytics routes file
@analytics_bp.route('/debug/analytics-data/<int:team_id>', methods=['GET'])
@jwt_required()
def debug_analytics_data(team_id):
    """Debug endpoint for analytics data."""
    try:
        with db_session() as session:  # Don't use read_only here to avoid the issue
            # Get team
            team = session.query(Team).get(team_id)
            if not team:
                return jsonify({'status': 'error', 'message': 'Team not found'}), 404
            
            # Get games
            games = session.query(Game).filter_by(team_id=team_id).all()
            games_data = [{
                'id': g.id,
                'date': str(g.date) if g.date else None,
                'opponent': g.opponent
            } for g in games]
            
            # Get batting orders
            batting_orders = session.query(BattingOrder).filter(
                BattingOrder.game_id.in_([g.id for g in games])
            ).all()
            batting_data = [{
                'game_id': bo.game_id,
                'format': 'list' if isinstance(bo.order_data, list) else 
                         ('dict_with_order_data' if isinstance(bo.order_data, dict) and 'order_data' in bo.order_data else 
                         'unknown'),
                'data_type': str(type(bo.order_data)),
                'has_data': bool(bo.order_data),
                'sample': str(bo.order_data)[:100] + '...' if bo.order_data else None
            } for bo in batting_orders]
            
            # Get fielding rotations
            fielding_query = session.query(FieldingRotation.game_id, 
                                          func.count(FieldingRotation.id).label('count')
                                         ).filter(
                FieldingRotation.game_id.in_([g.id for g in games])
            ).group_by(FieldingRotation.game_id).all()
            
            fielding_data = {game_id: count for game_id, count in fielding_query}
            
            # Games with both types of data
            complete_games = [
                game_id for game_id in [bo.game_id for bo in batting_orders]
                if game_id in fielding_data
            ]
            
            # Return diagnostic data
            return jsonify({
                'status': 'success',
                'team_id': team_id,
                'team_name': team.name,
                'games_count': len(games),
                'games_with_dates': len([g for g in games if g.date]),
                'batting_orders_count': len(batting_orders),
                'fielding_games_count': len(fielding_data),
                'complete_games_count': len(complete_games),
                'complete_games': complete_games,
                'data_checks': {
                    'has_games_with_dates': len([g for g in games if g.date]) > 0,
                    'has_batting_orders': len(batting_orders) > 0,
                    'has_fielding_rotations': len(fielding_data) > 0,
                    'has_complete_games': len(complete_games) > 0
                },
                'games': games_data,
                'batting_orders': batting_data,
                'fielding_games': fielding_data
            })
    except Exception as e:
        logging.error(f"Error in debug_analytics_data: {e}")
        return jsonify({
            'status': 'error',
            'team_id': team_id,
            'error': str(e)
        })