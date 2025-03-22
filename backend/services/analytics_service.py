"""
Analytics service for generating player statistics across games.
"""
from typing import Dict, List, Any
import logging
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import JSONB
from shared.db import db_session
from shared.models import Game, BattingOrder, FieldingRotation, PlayerAvailability, Player

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        player_stats = []
        
        with db_session(read_only=True) as session:
            # Get all players in the team
            players = session.query(Player).filter_by(team_id=team_id).all()
            
            # Get all games for this team
            games = session.query(Game).filter_by(team_id=team_id).all()
            game_ids = [game.id for game in games]
            
            # If no games, return empty stats
            if not game_ids:
                return []
            
            # Get all batting orders for these games
            batting_orders = session.query(BattingOrder).filter(
                BattingOrder.game_id.in_(game_ids)
            ).all()
            
            # Create a map of game_id to batting order
            game_to_batting = {}
            for bo in batting_orders:
                if bo.order_data:
                    game_to_batting[bo.game_id] = bo.order_data
            
            # Process stats for each player
            for player in players:
                stats = {
                    "player_id": player.id,
                    "name": player.full_name,
                    "jersey_number": player.jersey_number,
                    "total_games": len(games),
                    "games_in_lineup": 0,
                    "batting_positions": {},
                    "avg_batting_position": None,
                    "batting_position_history": []
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
                            "game_date": game.game_date.strftime("%Y-%m-%d") if game.game_date else None,
                            "opponent": game.opponent,
                            "position": position
                        })
                
                # Calculate summary statistics
                stats["games_in_lineup"] = len(positions)
                if positions:
                    stats["avg_batting_position"] = sum(positions) / len(positions)
                
                # Sort history by game date
                stats["batting_position_history"].sort(key=lambda x: x["game_date"] if x["game_date"] else "")
                
                player_stats.append(stats)
        
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
        player_stats = []
        
        with db_session(read_only=True) as session:
            # Get all players in the team
            players = session.query(Player).filter_by(team_id=team_id).all()
            
            # Get all games for this team
            games = session.query(Game).filter_by(team_id=team_id).all()
            game_ids = [game.id for game in games]
            
            # If no games, return empty stats
            if not game_ids:
                return []
            
            # Get all fielding rotations for these games
            fielding_rotations = session.query(FieldingRotation).filter(
                FieldingRotation.game_id.in_(game_ids)
            ).all()
            
            # Get all player availability data
            availability_data = session.query(PlayerAvailability).filter(
                PlayerAvailability.game_id.in_(game_ids)
            ).all()
            
            # Create a map of game_id and inning to positions
            game_inning_positions = {}
            for rotation in fielding_rotations:
                if rotation.positions:
                    if rotation.game_id not in game_inning_positions:
                        game_inning_positions[rotation.game_id] = {}
                    game_inning_positions[rotation.game_id][rotation.inning] = rotation.positions
            
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
                    "name": player.full_name,
                    "jersey_number": player.jersey_number,
                    "total_games": len(games),
                    "games_available": 0,
                    "games_unavailable": 0,
                    "total_innings": 0,
                    "infield_innings": 0,
                    "outfield_innings": 0,
                    "bench_innings": 0,
                    "position_count": {},
                    "position_history": []
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
                            if int(player_id) == player.id:
                                position = pos
                                break
                        
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
                            "game_date": game.game_date.strftime("%Y-%m-%d") if game.game_date else None,
                            "opponent": game.opponent,
                            "innings": game_positions
                        })
                
                # Sort history by game date
                stats["position_history"].sort(key=lambda x: x["game_date"] if x["game_date"] else "")
                
                player_stats.append(stats)
        
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
        with db_session(read_only=True) as session:
            # Get all games for this team
            games = session.query(Game).filter_by(team_id=team_id).all()
            
            # Basic team stats
            stats = {
                "team_id": team_id,
                "total_games": len(games),
                "games_by_month": {},
                "games_by_day": {
                    "Monday": 0,
                    "Tuesday": 0,
                    "Wednesday": 0,
                    "Thursday": 0,
                    "Friday": 0,
                    "Saturday": 0,
                    "Sunday": 0
                }
            }
            
            # Process game dates
            for game in games:
                if game.game_date:
                    # Count by month
                    month = game.game_date.strftime("%Y-%m")
                    stats["games_by_month"][month] = stats["games_by_month"].get(month, 0) + 1
                    
                    # Count by day of week
                    day = game.game_date.strftime("%A")
                    stats["games_by_day"][day] += 1
            
            return stats