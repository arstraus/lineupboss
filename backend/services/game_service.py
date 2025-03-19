"""
Game service for handling game-related business logic.
"""
from sqlalchemy.orm import Session
from models.models import Game, Team, BattingOrder, FieldingRotation, PlayerAvailability, Player

class GameService:
    """Service for game operations."""
    
    @staticmethod
    def get_games_by_team(db: Session, team_id: int):
        """
        Get all games for a specific team.
        
        Args:
            db: Database session
            team_id: Team ID
            
        Returns:
            List of games for the team
        """
        return db.query(Game).filter(Game.team_id == team_id).all()
    
    @staticmethod
    def get_game(db: Session, game_id: int, user_id: int):
        """
        Get a specific game by ID, ensuring it belongs to one of the user's teams.
        
        Args:
            db: Database session
            game_id: Game ID
            user_id: User ID to verify ownership
            
        Returns:
            Game if found and owned by user, None otherwise
        """
        return db.query(Game).join(Team).filter(
            Game.id == game_id,
            Team.user_id == user_id
        ).first()
    
    @staticmethod
    def create_game(db: Session, game_data: dict, team_id: int):
        """
        Create a new game.
        
        Args:
            db: Database session
            game_data: Dictionary containing game data
            team_id: Team ID to assign the game to
            
        Returns:
            Newly created game
        """
        game = Game(
            team_id=team_id,
            game_number=game_data['game_number'],
            date=game_data.get('date'),
            time=game_data.get('time'),
            opponent=game_data.get('opponent', ''),
            innings=game_data.get('innings', 6)
        )
        
        db.add(game)
        db.flush()  # Flush to get the ID without committing
        
        return game
    
    @staticmethod
    def update_game(db: Session, game: Game, game_data: dict):
        """
        Update a game with new data.
        
        Args:
            db: Database session
            game: Game object to update
            game_data: Dictionary containing updated game data
            
        Returns:
            Updated game
        """
        if 'game_number' in game_data:
            game.game_number = game_data['game_number']
        if 'date' in game_data:
            game.date = game_data['date']
        if 'time' in game_data:
            game.time = game_data['time']
        if 'opponent' in game_data:
            game.opponent = game_data['opponent']
        if 'innings' in game_data:
            game.innings = game_data['innings']
        
        db.flush()  # Flush changes without committing
        
        return game
    
    @staticmethod
    def delete_game(db: Session, game: Game):
        """
        Delete a game.
        
        Args:
            db: Database session
            game: Game object to delete
            
        Returns:
            True if successful
        """
        # Explicitly delete related objects first to avoid recursion errors
        # Get game ID before deletion for logging
        game_id = game.id
        
        # Delete batting order if exists
        if hasattr(game, 'batting_order') and game.batting_order:
            db.delete(game.batting_order)
            
        # Delete fielding rotations
        if hasattr(game, 'fielding_rotations') and game.fielding_rotations:
            for rotation in list(game.fielding_rotations):
                db.delete(rotation)
                
        # Delete player availability records
        if hasattr(game, 'player_availability') and game.player_availability:
            for avail in list(game.player_availability):
                db.delete(avail)
                
        # Now delete the game itself
        db.delete(game)
        db.flush()  # Flush without committing
        
        print(f"Successfully deleted game ID: {game_id}")
        return True
    
    @staticmethod
    def get_batting_order(db: Session, game_id: int):
        """
        Get the batting order for a game.
        
        Args:
            db: Database session
            game_id: Game ID
            
        Returns:
            BattingOrder object if found, None otherwise
        """
        return db.query(BattingOrder).filter(BattingOrder.game_id == game_id).first()
    
    @staticmethod
    def create_or_update_batting_order(db: Session, game_id: int, order_data: dict):
        """
        Create or update a batting order.
        
        Args:
            db: Database session
            game_id: Game ID
            order_data: Dictionary containing batting order data
            
        Returns:
            Created or updated BattingOrder object
        """
        batting_order = db.query(BattingOrder).filter(BattingOrder.game_id == game_id).first()
        
        if batting_order:
            batting_order.order_data = order_data
        else:
            batting_order = BattingOrder(game_id=game_id, order_data=order_data)
            db.add(batting_order)
        
        db.flush()  # Flush changes without committing
        
        return batting_order
    
    @staticmethod
    def get_fielding_rotations(db: Session, game_id: int):
        """
        Get all fielding rotations for a game.
        
        Args:
            db: Database session
            game_id: Game ID
            
        Returns:
            List of FieldingRotation objects
        """
        return db.query(FieldingRotation).filter(FieldingRotation.game_id == game_id).all()
    
    @staticmethod
    def get_fielding_rotation_by_inning(db: Session, game_id: int, inning: int):
        """
        Get a specific fielding rotation by game and inning.
        
        Args:
            db: Database session
            game_id: Game ID
            inning: Inning number
            
        Returns:
            FieldingRotation object if found, None otherwise
        """
        return db.query(FieldingRotation).filter(
            FieldingRotation.game_id == game_id,
            FieldingRotation.inning == inning
        ).first()
    
    @staticmethod
    def create_or_update_fielding_rotation(db: Session, game_id: int, inning: int, positions: dict):
        """
        Create or update a fielding rotation.
        
        Args:
            db: Database session
            game_id: Game ID
            inning: Inning number
            positions: Dictionary containing position assignments
            
        Returns:
            Created or updated FieldingRotation object
        """
        rotation = db.query(FieldingRotation).filter(
            FieldingRotation.game_id == game_id,
            FieldingRotation.inning == inning
        ).first()
        
        if rotation:
            rotation.positions = positions
        else:
            rotation = FieldingRotation(game_id=game_id, inning=inning, positions=positions)
            db.add(rotation)
        
        db.flush()  # Flush changes without committing
        
        return rotation
    
    @staticmethod
    def get_player_availability(db: Session, game_id: int):
        """
        Get availability status for all players in a game.
        
        Args:
            db: Database session
            game_id: Game ID
            
        Returns:
            List of PlayerAvailability objects
        """
        return db.query(PlayerAvailability).filter(PlayerAvailability.game_id == game_id).all()
    
    @staticmethod
    def get_player_availability_by_player(db: Session, game_id: int, player_id: int):
        """
        Get availability status for a specific player in a game.
        
        Args:
            db: Database session
            game_id: Game ID
            player_id: Player ID
            
        Returns:
            PlayerAvailability object if found, None otherwise
        """
        return db.query(PlayerAvailability).filter(
            PlayerAvailability.game_id == game_id,
            PlayerAvailability.player_id == player_id
        ).first()
        
    @staticmethod
    def get_player_availability_by_id(db: Session, game_id: int, player_id: int):
        """
        Get availability status for a specific player in a game.
        This is an alias for get_player_availability_by_player for API consistency.
        
        Args:
            db: Database session
            game_id: Game ID
            player_id: Player ID
            
        Returns:
            PlayerAvailability object if found, None otherwise
        """
        return GameService.get_player_availability_by_player(db, game_id, player_id)
    
    @staticmethod
    def set_player_availability(db: Session, game_id: int, player_id: int, available: bool, can_play_catcher: bool = False):
        """
        Set availability status for a player in a game.
        
        Args:
            db: Database session
            game_id: Game ID
            player_id: Player ID
            available: Whether the player is available
            can_play_catcher: Whether the player can play catcher
            
        Returns:
            Created or updated PlayerAvailability object
        """
        availability = db.query(PlayerAvailability).filter(
            PlayerAvailability.game_id == game_id,
            PlayerAvailability.player_id == player_id
        ).first()
        
        if availability:
            availability.available = available
            availability.can_play_catcher = can_play_catcher
        else:
            availability = PlayerAvailability(
                game_id=game_id,
                player_id=player_id,
                available=available,
                can_play_catcher=can_play_catcher
            )
            db.add(availability)
        
        db.flush()  # Flush changes without committing
        
        return availability
    
    @staticmethod
    def batch_set_player_availability(db: Session, game_id: int, availability_data: list):
        """
        Set availability status for multiple players in a game.
        
        Args:
            db: Database session
            game_id: Game ID
            availability_data: List of dictionaries containing player_id, available, and can_play_catcher
            
        Returns:
            List of created or updated PlayerAvailability objects
        """
        result = []
        
        for data in availability_data:
            player_id = data['player_id']
            available = data.get('available', True)
            can_play_catcher = data.get('can_play_catcher', False)
            
            availability = GameService.set_player_availability(
                db, game_id, player_id, available, can_play_catcher
            )
            
            result.append(availability)
        
        # No need to commit here, as the db_session in the controller will handle it
        # Each set_player_availability call will flush its changes
        
        return result
    
    @staticmethod
    def serialize_game(game: Game):
        """
        Serialize a game object to a dictionary.
        
        Args:
            game: Game object
            
        Returns:
            Dictionary representing the game
        """
        return {
            'id': game.id,
            'team_id': game.team_id,
            'game_number': game.game_number,
            # Format date in ISO format with explicit string formatting to avoid timezone issues
            'date': game.date.isoformat() if game.date else None,
            'time': str(game.time) if game.time else None,
            'opponent': game.opponent,
            'innings': game.innings
        }
    
    @staticmethod
    def serialize_batting_order(batting_order: BattingOrder):
        """
        Serialize a batting order object to a dictionary.
        
        Args:
            batting_order: BattingOrder object
            
        Returns:
            Dictionary representing the batting order
        """
        return {
            'id': batting_order.id,
            'game_id': batting_order.game_id,
            'order_data': batting_order.order_data
        }
    
    @staticmethod
    def serialize_fielding_rotation(rotation: FieldingRotation):
        """
        Serialize a fielding rotation object to a dictionary.
        
        Args:
            rotation: FieldingRotation object
            
        Returns:
            Dictionary representing the fielding rotation
        """
        return {
            'id': rotation.id,
            'game_id': rotation.game_id,
            'inning': rotation.inning,
            'positions': rotation.positions
        }
    
    @staticmethod
    def serialize_player_availability(availability: PlayerAvailability, include_player: bool = False):
        """
        Serialize a player availability object to a dictionary.
        
        Args:
            availability: PlayerAvailability object
            include_player: Whether to include player details
            
        Returns:
            Dictionary representing the player availability
        """
        result = {
            'id': availability.id,
            'game_id': availability.game_id,
            'player_id': availability.player_id,
            'available': availability.available,
            'can_play_catcher': availability.can_play_catcher
        }
        
        if include_player and availability.player:
            result['player'] = {
                'id': availability.player.id,
                'first_name': availability.player.first_name,
                'last_name': availability.player.last_name,
                'jersey_number': availability.player.jersey_number,
                'full_name': availability.player.full_name()
            }
        
        return result