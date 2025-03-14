"""
Player service for handling player-related business logic.
"""
from sqlalchemy.orm import Session
from models.models import Player, Team

class PlayerService:
    """Service for player operations."""
    
    @staticmethod
    def get_players_by_team(db: Session, team_id: int):
        """
        Get all players for a specific team.
        
        Args:
            db: Database session
            team_id: Team ID
            
        Returns:
            List of players for the team
        """
        return db.query(Player).filter(Player.team_id == team_id).all()
    
    @staticmethod
    def get_player(db: Session, player_id: int, user_id: int):
        """
        Get a specific player by ID, ensuring it belongs to one of the user's teams.
        
        Args:
            db: Database session
            player_id: Player ID
            user_id: User ID to verify ownership
            
        Returns:
            Player if found and owned by user, None otherwise
        """
        return db.query(Player).join(Team).filter(
            Player.id == player_id,
            Team.user_id == user_id
        ).first()
    
    @staticmethod
    def create_player(db: Session, player_data: dict, team_id: int):
        """
        Create a new player.
        
        Args:
            db: Database session
            player_data: Dictionary containing player data
            team_id: Team ID to assign the player to
            
        Returns:
            Newly created player
        """
        player = Player(
            team_id=team_id,
            first_name=player_data['first_name'],
            last_name=player_data['last_name'],
            jersey_number=player_data['jersey_number']
        )
        
        db.add(player)
        db.commit()
        db.refresh(player)
        
        return player
    
    @staticmethod
    def update_player(db: Session, player: Player, player_data: dict):
        """
        Update a player with new data.
        
        Args:
            db: Database session
            player: Player object to update
            player_data: Dictionary containing updated player data
            
        Returns:
            Updated player
        """
        if 'first_name' in player_data:
            player.first_name = player_data['first_name']
        if 'last_name' in player_data:
            player.last_name = player_data['last_name']
        if 'jersey_number' in player_data:
            player.jersey_number = player_data['jersey_number']
        
        db.commit()
        db.refresh(player)
        
        return player
    
    @staticmethod
    def delete_player(db: Session, player: Player):
        """
        Delete a player.
        
        Args:
            db: Database session
            player: Player object to delete
            
        Returns:
            True if successful
        """
        db.delete(player)
        db.commit()
        
        return True
    
    @staticmethod
    def serialize_player(player: Player):
        """
        Serialize a player object to a dictionary.
        
        Args:
            player: Player object
            
        Returns:
            Dictionary representing the player
        """
        return {
            'id': player.id,
            'team_id': player.team_id,
            'first_name': player.first_name,
            'last_name': player.last_name,
            'jersey_number': player.jersey_number,
            'full_name': player.full_name()
        }