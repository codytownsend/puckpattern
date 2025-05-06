import argparse
import logging
import sys
from datetime import datetime

from sqlalchemy.orm import Session

# Add parent directory to path for imports
import os
import sys
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(parent_dir)

from app.db.session import get_db, SessionLocal
from app.data_import.import_service import NHLImportService


def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("import.log")
        ]
    )
    return logging.getLogger(__name__)


def import_teams(db: Session):
    """Import all NHL teams."""
    service = NHLImportService(db)
    teams = service.import_teams()
    return len(teams)


def import_roster(db: Session, team_id: str):
    """Import roster for a specific team."""
    service = NHLImportService(db)
    players = service.import_team_roster(team_id)
    return len(players)


def import_all_rosters(db: Session):
    """Import rosters for all teams."""
    service = NHLImportService(db)
    
    # First import teams
    teams = service.import_teams()
    
    total_players = 0
    for team in teams:
        players = service.import_team_roster(team.team_id)
        total_players += len(players)
    
    return total_players


def import_game(db: Session, game_id: str):
    """Import a specific game with events."""
    service = NHLImportService(db)
    game = service.import_game(game_id, fetch_events=True)
    return 1 if game else 0


def import_schedule(db: Session, start_date: str, end_date: str, team_id: str = None):
    """Import schedule for a date range."""
    service = NHLImportService(db)
    games = service.import_schedule(start_date, end_date, team_id)
    return len(games)


def import_season(db: Session, season: str, team_id: str = None):
    """Import all games for a season."""
    service = NHLImportService(db)
    games = service.import_season(season, team_id)
    return len(games)


def main():
    parser = argparse.ArgumentParser(description="Import NHL data to PuckPattern")
    
    subparsers = parser.add_subparsers(dest="command", help="Import command")
    
    # Teams parser
    teams_parser = subparsers.add_parser("teams", help="Import all NHL teams")
    
    # Roster parser
    roster_parser = subparsers.add_parser("roster", help="Import team roster")
    roster_parser.add_argument("--team-id", type=str, help="NHL team ID")
    roster_parser.add_argument("--all", action="store_true", help="Import all team rosters")
    
    # Game parser
    game_parser = subparsers.add_parser("game", help="Import a specific game")
    game_parser.add_argument("--game-id", type=str, required=True, help="NHL game ID")
    
    # Schedule parser
    schedule_parser = subparsers.add_parser("schedule", help="Import schedule for date range")
    schedule_parser.add_argument("--start-date", type=str, required=True, help="Start date (YYYY-MM-DD)")
    schedule_parser.add_argument("--end-date", type=str, required=True, help="End date (YYYY-MM-DD)")
    schedule_parser.add_argument("--team-id", type=str, help="NHL team ID (optional)")
    
    # Season parser
    season_parser = subparsers.add_parser("season", help="Import all games for a season")
    season_parser.add_argument("--season", type=str, required=True, help="Season (e.g., 20222023)")
    season_parser.add_argument("--team-id", type=str, help="NHL team ID (optional)")
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    
    logger = setup_logging()
    
    # Get database session
    db = SessionLocal()
    
    try:
        start_time = datetime.now()
        logger.info(f"Starting import: {args.command}")
        
        if args.command == "teams":
            count = import_teams(db)
            logger.info(f"Imported {count} teams")
            
        elif args.command == "roster":
            if args.all:
                count = import_all_rosters(db)
                logger.info(f"Imported {count} players across all teams")
            elif args.team_id:
                count = import_roster(db, args.team_id)
                logger.info(f"Imported {count} players for team {args.team_id}")
            else:
                logger.error("Either --team-id or --all is required for roster import")
                sys.exit(1)
                
        elif args.command == "game":
            count = import_game(db, args.game_id)
            logger.info(f"Imported {count} games")
            
        elif args.command == "schedule":
            count = import_schedule(db, args.start_date, args.end_date, args.team_id)
            logger.info(f"Imported {count} games")
            
        elif args.command == "season":
            count = import_season(db, args.season, args.team_id)
            logger.info(f"Imported {count} games for season {args.season}")
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.info(f"Import completed in {duration:.2f} seconds")
        
    except Exception as e:
        logger.exception(f"Error during import: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()