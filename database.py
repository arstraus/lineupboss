"""
Database utilities for LineupBoss main application.

This file re-exports the shared database utilities to maintain compatibility with existing imports.
"""
from shared.models import (
    Base, User, Team, Player, Game, 
    BattingOrder, FieldingRotation, PlayerAvailability
)
from shared.database import (
    create_tables, get_db_session, db_session,
    serialize_player, serialize_game
)
from shared.auth import (
    create_user, verify_user, get_teams_for_user,
    get_teams_with_details_for_user, create_team_with_user
)

def delete_team(team_id):
    """Delete a team and all its associated data from the database"""
    with db_session() as session:
        try:
            # Find the team
            team = session.query(Team).filter(Team.id == team_id).one()
            
            # Store name for confirmation message
            team_name = team.name
            
            # The cascading delete set up in the database models should handle
            # deleting all the related data (players, games, etc.)
            session.delete(team)
            session.commit()
            
            return True, team_name
        except Exception as e:
            session.rollback()
            return False, str(e)

# Initialize the database (run this when setting up the app)
if __name__ == "__main__":
    create_tables()
    print("Database tables created successfully")