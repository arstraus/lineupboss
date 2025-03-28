"""
Analytics service for generating player statistics across games.
"""
from typing import Dict, List, Any
import logging
import traceback

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Safe imports with fallbacks
try:
    from sqlalchemy import func
    from sqlalchemy.dialects.postgresql import JSONB
    # Update to use the correct database module paths
    from database import db_session
    from utils import standardize_error_response as db_error_response
    from models.models import Game, BattingOrder, FieldingRotation, PlayerAvailability, Player
    logger.info("Successfully imported all required modules for AnalyticsService")
    HAS_DB_DEPENDENCIES = True
except ImportError as e:
    logger.error(f"Failed to import a module for AnalyticsService: {str(e)}")
    logger.error(traceback.format_exc())
    # Provide dummy objects for graceful degradation
    HAS_DB_DEPENDENCIES = False
    
    class Game: pass
    class BattingOrder: pass
    class FieldingRotation: pass
    class PlayerAvailability: pass
    class Player: pass
    
    # Create a dummy db_session context manager
    def db_session(read_only=False, commit=False):
        class DummyContextManager:
            def __enter__(self):
                logger.error("Using dummy db_session - database access will fail")
                return None
            def __exit__(self, exc_type, exc_val, exc_tb):
                pass
        return DummyContextManager()
    
    # Create a dummy error response function
    def db_error_response(error, message):
        logger.error(f"Database error: {message} - {str(error)}")
        return {"error": message}, 500

class AnalyticsService:
    """Service for analytics operations."""
    
    @staticmethod
    def get_player_batting_analytics(team_id: int) -> List[Dict[str, Any]]:
        """
        Get batting analytics for all players in a team across all games.
        
        Args:
            team_id: Team ID
            
        Returns:
            List of player batting analytics
        """
        logger.info(f"Fetching batting analytics for team_id: {team_id}")
        
        # Check if we have all required dependencies
        if not HAS_DB_DEPENDENCIES:
            logger.error("Cannot fetch batting analytics: missing database dependencies")
            return []
        player_stats = []
        
        with db_session(read_only=True) as session:
            # Get all players in the team
            players = session.query(Player).filter_by(team_id=team_id).all()
            logger.info(f"Found {len(players)} players for team {team_id}")
            
            # Get all games for this team
            games = session.query(Game).filter_by(team_id=team_id).all()
            game_ids = [game.id for game in games]
            logger.info(f"Found {len(games)} games for team {team_id}: {game_ids}")
            
            # If no games, return empty stats
            if not game_ids:
                logger.info(f"No games found for team {team_id}, returning empty stats")
                return []
            
            # Get all batting orders for these games
            batting_orders = session.query(BattingOrder).filter(
                BattingOrder.game_id.in_(game_ids)
            ).all()
            logger.info(f"Found {len(batting_orders)} batting orders for team {team_id}")
            
            # Create a map of game_id to batting order
            game_to_batting = {}
            for bo in batting_orders:
                if bo.order_data:
                    # Handle both possible formats of batting order data
                    if isinstance(bo.order_data, list):
                        # Direct array of player IDs
                        game_to_batting[bo.game_id] = bo.order_data
                        logger.info(f"Game {bo.game_id} has batting order (list format): {bo.order_data}")
                    elif isinstance(bo.order_data, dict) and 'order_data' in bo.order_data:
                        # Object with order_data field containing array
                        game_to_batting[bo.game_id] = bo.order_data['order_data']
                        logger.info(f"Game {bo.game_id} has batting order (dict format): {bo.order_data['order_data']}")
                    else:
                        logger.warning(f"Game {bo.game_id} has unrecognized batting order format: {type(bo.order_data)}")
                else:
                    logger.info(f"Game {bo.game_id} has empty batting order data")
            
            logger.info(f"Created batting order map with {len(game_to_batting)} entries")
            
            # Process stats for each player
            for player in players:
                stats = {
                    "player_id": player.id,
                    "name": player.full_name(),
                    "jersey_number": player.jersey_number,
                    "total_games": len(games),
                    "games_in_lineup": 0,
                    "batting_positions": {},
                    "avg_batting_position": None,
                    "batting_position_history": [],
                    "has_data": False  # Flag to indicate if we have real data
                }
                
                # Track batting positions across games
                positions = []
                
                for game in games:
                    if game.id in game_to_batting and player.id in game_to_batting[game.id]:
                        # Player was in the batting order for this game
                        position = game_to_batting[game.id].index(player.id) + 1
                        positions.append(position)
                        
                        # Increment the count for this position
                        stats["batting_positions"][position] = stats["batting_positions"].get(position, 0) + 1
                        
                        # Add to history
                        stats["batting_position_history"].append({
                            "game_id": game.id,
                            "game_date": game.game_date.strftime("%Y-%m-%d") if hasattr(game, 'game_date') and game.game_date else None,
                            "opponent": game.opponent,
                            "position": position
                        })
                
                # Calculate summary statistics
                stats["games_in_lineup"] = len(positions)
                if positions:
                    stats["avg_batting_position"] = sum(positions) / len(positions)
                    stats["has_data"] = True
                
                # Sort history by game date
                stats["batting_position_history"].sort(key=lambda x: x["game_date"] if x["game_date"] else "")
                
                # Always return stats for players, even if empty
                player_stats.append(stats)
                logger.info(f"Player {player.id} ({player.full_name()}): found {len(positions)} batting positions")
        
        return player_stats
    
    @staticmethod
    def get_player_fielding_analytics(team_id: int) -> List[Dict[str, Any]]:
        """
        Get fielding analytics for all players in a team across all games.
        
        Args:
            team_id: Team ID
            
        Returns:
            List of player fielding analytics
        """
        logger.info(f"Fetching fielding analytics for team_id: {team_id}")
        
        # Check if we have all required dependencies
        if not HAS_DB_DEPENDENCIES:
            logger.error("Cannot fetch fielding analytics: missing database dependencies")
            return []
        player_stats = []
        
        with db_session(read_only=True) as session:
            # Get all players in the team
            players = session.query(Player).filter_by(team_id=team_id).all()
            logger.info(f"Found {len(players)} players for team {team_id}")
            
            # Get all games for this team
            games = session.query(Game).filter_by(team_id=team_id).all()
            game_ids = [game.id for game in games]
            logger.info(f"Found {len(games)} games for team {team_id}: {game_ids}")
            
            # If no games, return empty stats
            if not game_ids:
                logger.info(f"No games found for team {team_id}, returning empty stats")
                return []
            
            # Get all fielding rotations for these games
            fielding_rotations = session.query(FieldingRotation).filter(
                FieldingRotation.game_id.in_(game_ids)
            ).all()
            logger.info(f"Found {len(fielding_rotations)} fielding rotation records for team {team_id}")
            
            # Get all player availability data
            availability_data = session.query(PlayerAvailability).filter(
                PlayerAvailability.game_id.in_(game_ids)
            ).all()
            logger.info(f"Found {len(availability_data)} player availability records for team {team_id}")
            
            # Create a map of game_id and inning to positions
            game_inning_positions = {}
            for rotation in fielding_rotations:
                if rotation.positions:
                    if rotation.game_id not in game_inning_positions:
                        game_inning_positions[rotation.game_id] = {}
                    game_inning_positions[rotation.game_id][rotation.inning] = rotation.positions
                    logger.info(f"Game {rotation.game_id}, Inning {rotation.inning} has positions: {rotation.positions}")
                else:
                    logger.info(f"Game {rotation.game_id}, Inning {rotation.inning} has empty positions data")
            
            logger.info(f"Created fielding position map with {len(game_inning_positions)} game entries")
            
            # Create a map of game_id to player availability
            game_player_availability = {}
            for availability in availability_data:
                if availability.game_id not in game_player_availability:
                    game_player_availability[availability.game_id] = {}
                game_player_availability[availability.game_id][availability.player_id] = availability.available
            
            # Constants for position categories
            INFIELD = ["Pitcher", "1B", "2B", "3B", "SS"]
            OUTFIELD = ["Catcher", "LF", "RF", "LC", "RC"]
            BENCH = "Bench"
            
            # Process stats for each player
            for player in players:
                stats = {
                    "player_id": player.id,
                    "name": player.full_name(),
                    "jersey_number": player.jersey_number,
                    "total_games": len(games),
                    "games_available": 0,
                    "games_unavailable": 0,
                    "total_innings": 0,
                    "infield_innings": 0,
                    "outfield_innings": 0,
                    "bench_innings": 0,
                    "position_count": {},
                    "position_history": [],
                    "has_data": False  # Flag to indicate if we have real data
                }
                
                for game in games:
                    # Check availability
                    available = True
                    if game.id in game_player_availability and player.id in game_player_availability[game.id]:
                        available = game_player_availability[game.id][player.id]
                    
                    if available:
                        stats["games_available"] += 1
                    else:
                        stats["games_unavailable"] += 1
                        continue  # Skip unavailable games
                    
                    # Skip games with no fielding data
                    if game.id not in game_inning_positions:
                        continue
                    
                    # Track positions for each inning
                    game_positions = []
                    
                    for inning, positions in game_inning_positions[game.id].items():
                        stats["total_innings"] += 1
                        
                        # Find this player's position in this inning
                        position = BENCH  # Default to bench
                        for pos, player_id in positions.items():
                            try:
                                # Handle case where player_id might be a string or number
                                if isinstance(player_id, int) and player_id == player.id:
                                    position = pos
                                    break
                                elif isinstance(player_id, str) and player_id.isdigit() and int(player_id) == player.id:
                                    position = pos
                                    break
                            except (ValueError, TypeError):
                                logger.warning(f"Invalid player ID format: {player_id} for position {pos}")
                                continue
                        
                        # Count by position category
                        if position in INFIELD:
                            stats["infield_innings"] += 1
                        elif position in OUTFIELD:
                            stats["outfield_innings"] += 1
                        else:
                            stats["bench_innings"] += 1
                        
                        # Count specific positions
                        stats["position_count"][position] = stats["position_count"].get(position, 0) + 1
                        
                        # Add to history
                        game_positions.append({
                            "inning": inning,
                            "position": position
                        })
                    
                    # Add game summary to history
                    if game_positions:
                        stats["position_history"].append({
                            "game_id": game.id,
                            "game_date": game.game_date.strftime("%Y-%m-%d") if hasattr(game, 'game_date') and game.game_date else None,
                            "opponent": game.opponent,
                            "innings": game_positions
                        })
                        stats["has_data"] = True  # We found some position data for this player
                
                # Sort history by game date
                stats["position_history"].sort(key=lambda x: x["game_date"] if x["game_date"] else "")
                
                # Always return stats for players, even if empty
                player_stats.append(stats)
                logger.info(f"Player {player.id} ({player.full_name()}): found {stats['infield_innings'] + stats['outfield_innings']} fielding assignments")
        
        return player_stats
    
    @staticmethod
    def get_team_analytics(team_id: int) -> Dict[str, Any]:
        """
        Get team analytics across all games.
        
        Args:
            team_id: Team ID
            
        Returns:
            Team analytics
        """
        logger.info(f"Fetching team analytics for team_id: {team_id}")
        
        # Check if we have all required dependencies
        if not HAS_DB_DEPENDENCIES:
            logger.error("Cannot fetch team analytics: missing database dependencies")
            return {
                "team_id": team_id,
                "total_games": 0,
                "games_by_month": {},
                "games_by_day": {"Monday": 0, "Tuesday": 0, "Wednesday": 0, 
                                "Thursday": 0, "Friday": 0, "Saturday": 0, "Sunday": 0},
                "has_data": False,
                "error": "Missing database dependencies"
            }
        with db_session(read_only=True) as session:
            # Get all games for this team
            games = session.query(Game).filter_by(team_id=team_id).all()
            logger.info(f"Found {len(games)} games for team {team_id}")
            
            # Basic team stats
            stats = {
                "team_id": team_id,
                "total_games": 0,  # Will be updated after filtering games with data
                "games_by_month": {},
                "games_by_day": {
                    "Monday": 0,
                    "Tuesday": 0,
                    "Wednesday": 0,
                    "Thursday": 0,
                    "Friday": 0,
                    "Saturday": 0,
                    "Sunday": 0
                },
                "has_data": False  # Will be updated based on data availability
            }
            
            # Get all games with dates
            games_with_dates = [g for g in games if hasattr(g, 'game_date') and g.game_date]
            logger.info(f"Found {len(games_with_dates)} games with dates for team {team_id}")
            
            if not games_with_dates:
                logger.info(f"No games with dates found for team {team_id}")
                return stats
            
            # Get batting orders for these games
            game_ids = [g.id for g in games_with_dates]
            batting_orders = session.query(BattingOrder).filter(
                BattingOrder.game_id.in_(game_ids)
            ).all()
            logger.info(f"Found {len(batting_orders)} batting orders for team {team_id}")
            
            # Create a map of game_id to batting order
            game_to_batting = {}
            for bo in batting_orders:
                if bo.order_data:
                    # Handle both possible formats of batting order data
                    if isinstance(bo.order_data, list):
                        game_to_batting[bo.game_id] = bo.order_data
                    elif isinstance(bo.order_data, dict) and 'order_data' in bo.order_data:
                        game_to_batting[bo.game_id] = bo.order_data['order_data']
            
            # Get fielding rotations for these games
            fielding_query = session.query(FieldingRotation.game_id, 
                                          func.count(FieldingRotation.id).label('count')
                                         ).filter(
                FieldingRotation.game_id.in_(game_ids)
            ).group_by(FieldingRotation.game_id).all()
            
            fielding_games = {game_id: count for game_id, count in fielding_query}
            logger.info(f"Found {len(fielding_games)} games with fielding rotations for team {team_id}")
            
            # Find games with both batting and fielding data
            games_with_both = [
                game for game in games_with_dates
                if game.id in game_to_batting and game.id in fielding_games
            ]
            
            logger.info(f"Found {len(games_with_both)} games with both batting and fielding data for team {team_id}")
            
            # Update has_data flag based on whether any valid games were found
            stats["has_data"] = len(games_with_both) > 0
            
            # Only process games with both batting and fielding data for analytics
            if games_with_both:
                stats["total_games"] = len(games_with_both)
                
                # Process game dates
                for game in games_with_both:
                    if hasattr(game, 'game_date') and game.game_date:
                        # Count by month
                        month = game.game_date.strftime("%Y-%m")
                        stats["games_by_month"][month] = stats["games_by_month"].get(month, 0) + 1
                        
                        # Count by day of week
                        day = game.game_date.strftime("%A")
                        stats["games_by_day"][day] += 1
            
            logger.info(f"Team {team_id} analytics: total_games={stats['total_games']}, months={len(stats['games_by_month'])}, has_data={stats['has_data']}")
            return stats