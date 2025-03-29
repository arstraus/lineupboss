#!/usr/bin/env python3
"""
Script to check game data and fix missing dates.
"""
from database import db_session
from models.models import Game
from datetime import datetime, timedelta
import sys

def check_games(team_id):
    """Check games for the specified team."""
    with db_session(read_only=True) as session:
        games = session.query(Game).filter_by(team_id=team_id).all()
        print(f"Found {len(games)} games for team {team_id}")
        
        for i, game in enumerate(games):
            print(f"Game {game.id}: {game.opponent}, Date: {game.game_date}")
            
        # Check how many games have dates
        games_with_dates = [g for g in games if g.game_date is not None]
        print(f"\nGames with dates: {len(games_with_dates)} out of {len(games)}")
        
        return games

def fix_game_dates(team_id):
    """Add missing dates to games."""
    with db_session(commit=True) as session:
        games = session.query(Game).filter_by(team_id=team_id).all()
        
        # Base date - start from a month ago
        base_date = datetime.now() - timedelta(days=30)
        
        updated_count = 0
        for i, game in enumerate(games):
            if game.game_date is None:
                # Assign a date starting from base_date, spread 3 days apart
                game_date = base_date + timedelta(days=i*3)
                game.game_date = game_date
                print(f"Updated Game {game.id}: {game.opponent} with date {game_date.strftime('%Y-%m-%d')}")
                updated_count += 1
        
        print(f"\nUpdated {updated_count} games with dates")
        
        # Commit is automatic with db_session(commit=True)
        
        return updated_count

if __name__ == "__main__":
    team_id = 2  # Default team ID
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "check":
            check_games(team_id)
        elif sys.argv[1] == "fix":
            fix_game_dates(team_id)
            check_games(team_id)  # Verify changes
        else:
            print(f"Unknown command: {sys.argv[1]}")
            print("Usage: python check_games.py [check|fix]")
    else:
        print("Checking games...")
        check_games(team_id)
        print("\nTo fix missing dates, run: python check_games.py fix")