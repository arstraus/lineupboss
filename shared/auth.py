"""
Shared authentication utilities for LineupBoss.

This module provides common user authentication functions for the application.
"""
from shared.database import get_db_session, db_session
from shared.models import User

def create_user(email, password):
    """Create a new user"""
    with db_session() as session:
        try:
            # Check if user already exists
            existing_user = session.query(User).filter(User.email == email).first()
            if existing_user:
                return None, "Email already registered"
                
            user = User(email=email)
            user.set_password(password)
            session.add(user)
            session.commit()
            return user.id, "User created successfully"
        except Exception as e:
            session.rollback()
            return None, str(e)

def verify_user(email, password):
    """Verify user credentials"""
    with db_session() as session:
        user = session.query(User).filter(User.email == email).first()
        if user and user.check_password(password):
            return user.id
        return None

def get_user_by_id(user_id):
    """Get user by ID"""
    with db_session() as session:
        user = session.query(User).filter(User.id == user_id).first()
        return user

def get_teams_for_user(user_id):
    """Get all teams owned by a specific user"""
    from shared.models import Team
    with db_session() as session:
        teams = session.query(Team).filter(
            (Team.user_id == user_id) | (Team.user_id == None)
        ).all()
        return [(team.id, team.name) for team in teams]

def get_teams_with_details_for_user(user_id):
    """Get all teams with details owned by a specific user"""
    from shared.models import Team
    with db_session() as session:
        teams = session.query(Team).filter(
            (Team.user_id == user_id) | (Team.user_id == None)
        ).all()
        team_details = []
        for team in teams:
            team_details.append({
                "id": team.id, 
                "name": team.name,
                "league": team.league,
                "head_coach": team.head_coach
            })
        return team_details
        
def create_team_with_user(team_info, user_id):
    """Create a new team with user ownership"""
    from shared.models import Team
    with db_session() as session:
        try:
            team = Team(
                name=team_info["team_name"],
                league=team_info.get("league", ""),
                head_coach=team_info.get("head_coach", ""),
                assistant_coach1=team_info.get("assistant_coach1", ""),
                assistant_coach2=team_info.get("assistant_coach2", ""),
                user_id=user_id
            )
            session.add(team)
            session.commit()
            return team.id
        except Exception as e:
            session.rollback()
            print(f"Error creating team: {e}")
            return None