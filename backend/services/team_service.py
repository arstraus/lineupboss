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
        """
        team = Team(
            name=team_data['name'],
            league=team_data.get('league', ''),
            head_coach=team_data.get('head_coach', ''),
            assistant_coach1=team_data.get('assistant_coach1', ''),
            assistant_coach2=team_data.get('assistant_coach2', ''),
            user_id=user_id
        )
        
        db.add(team)
        db.commit()
        db.refresh(team)
        
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
        
        db.commit()
        db.refresh(team)
        
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
        """
        db.delete(team)
        db.commit()
        
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