"""
Team service for handling team-related business logic.
"""
from sqlalchemy.orm import Session
from models.models import Team

class TeamService:
    """Service for team operations."""

    @staticmethod
    def get_teams_by_user(db: Session, user_id: int):
        """
        Get all teams owned by a user.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            List of teams owned by the user
        """
        return db.query(Team).filter(Team.user_id == user_id).all()
    
    @staticmethod
    def get_team(db: Session, team_id: int, user_id: int):
        """
        Get a specific team by ID, ensuring it belongs to the user.
        
        Args:
            db: Database session
            team_id: Team ID
            user_id: User ID to verify ownership
            
        Returns:
            Team if found and owned by user, None otherwise
        """
        return db.query(Team).filter(Team.id == team_id, Team.user_id == user_id).first()
    
    @staticmethod
    def create_team(db: Session, team_data: dict, user_id: int):
        """
        Create a new team.
        
        Args:
            db: Database session
            team_data: Dictionary containing team data
            user_id: User ID to assign as owner
            
        Returns:
            Newly created team
            
        Note:
            This method doesn't commit changes to the database.
            The caller is responsible for committing the transaction.
        """
        team = Team(
            name=team_data['name'],
            league=team_data.get('league', ''),
            head_coach=team_data.get('head_coach', ''),
            assistant_coach1=team_data.get('assistant_coach1', ''),
            assistant_coach2=team_data.get('assistant_coach2', ''),
            user_id=user_id
        )
        
        # Add to session but don't commit - caller will commit
        db.add(team)
        # Flush to get the ID generated
        db.flush()
        
        return team
    
    @staticmethod
    def update_team(db: Session, team: Team, team_data: dict):
        """
        Update a team with new data.
        
        Args:
            db: Database session
            team: Team object to update
            team_data: Dictionary containing updated team data
            
        Returns:
            Updated team
            
        Note:
            This method doesn't commit changes to the database.
            The caller is responsible for committing the transaction.
        """
        if 'name' in team_data:
            team.name = team_data['name']
        if 'league' in team_data:
            team.league = team_data['league']
        if 'head_coach' in team_data:
            team.head_coach = team_data['head_coach']
        if 'assistant_coach1' in team_data:
            team.assistant_coach1 = team_data['assistant_coach1']
        if 'assistant_coach2' in team_data:
            team.assistant_coach2 = team_data['assistant_coach2']
        
        # No commit here - caller will commit
        # But flush to ensure related objects are updated
        db.flush()
        
        return team
    
    @staticmethod
    def delete_team(db: Session, team: Team):
        """
        Delete a team.
        
        Args:
            db: Database session
            team: Team object to delete
            
        Returns:
            True if successful
            
        Note:
            This method doesn't commit changes to the database.
            The caller is responsible for committing the transaction.
        """
        # Get team ID before deletion for logging
        team_id = team.id
        
        # Use direct SQL to delete related records and avoid recursion issues
        # This bypasses SQLAlchemy's object management system that can cause recursion
        
        # Delete in order of most nested to least nested to respect foreign key constraints
        
        # Delete player availability records linked to this team's players
        db.execute(f"""
            DELETE FROM player_availability 
            WHERE player_id IN (SELECT id FROM players WHERE team_id = {team_id})
        """)
        
        # Delete fielding rotations for this team's games
        db.execute(f"""
            DELETE FROM fielding_rotations 
            WHERE game_id IN (SELECT id FROM games WHERE team_id = {team_id})
        """)
        
        # Delete batting orders for this team's games
        db.execute(f"""
            DELETE FROM batting_orders 
            WHERE game_id IN (SELECT id FROM games WHERE team_id = {team_id})
        """)
        
        # Delete players for this team
        db.execute(f"DELETE FROM players WHERE team_id = {team_id}")
        
        # Delete games for this team
        db.execute(f"DELETE FROM games WHERE team_id = {team_id}")
        
        # Finally delete the team itself
        db.execute(f"DELETE FROM teams WHERE id = {team_id}")
        
        # No need to delete the team object since we already removed it via SQL
        # Don't flush as the SQL has already been executed
        
        print(f"Successfully deleted team ID: {team_id} using direct SQL")
        return True
    
    @staticmethod
    def serialize_team(team: Team):
        """
        Serialize a team object to a dictionary.
        
        Args:
            team: Team object
            
        Returns:
            Dictionary representing the team
        """
        return {
            'id': team.id,
            'name': team.name,
            'league': team.league,
            'head_coach': team.head_coach,
            'assistant_coach1': team.assistant_coach1,
            'assistant_coach2': team.assistant_coach2
        }