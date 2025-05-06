import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.base import Team, Player, Game, GameEvent
from app.models.analytics import ShotEvent, ZoneEntry, Pass, PuckRecovery, TeamGameStats, PlayerGameStats
from app.data_import.nhl_data_fetcher import NHLDataFetcher
from app.data_import.event_processor import EventProcessor

logger = logging.getLogger(__name__)


class NHLImportService:
    """
    Service for importing NHL data into the PuckPattern database.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.fetcher = NHLDataFetcher()
        self.event_processor = EventProcessor(db)
    
    def import_teams(self) -> List[Team]:
        """
        Import all NHL teams.
        
        Returns:
            List of created or updated teams
        """
        logger.info("Importing NHL teams")
        nhl_teams = self.fetcher.get_teams()
        
        teams = []
        for team_data in nhl_teams:
            team_id = str(team_data["id"])
            
            # Check if team already exists
            db_team = self.db.query(Team).filter(Team.team_id == team_id).first()
            
            if db_team:
                # Update existing team
                db_team.name = team_data["name"]
                db_team.abbreviation = team_data["abbreviation"]
                logger.debug(f"Updated team: {db_team.name}")
            else:
                # Create new team
                db_team = Team(
                    team_id=team_id,
                    name=team_data["name"],
                    abbreviation=team_data["abbreviation"]
                )
                self.db.add(db_team)
                logger.debug(f"Created team: {db_team.name}")
            
            teams.append(db_team)
        
        self.db.commit()
        logger.info(f"Imported {len(teams)} teams")
        return teams
    
    def import_team_roster(self, team_id: str) -> List[Player]:
        """
        Import roster for a specific team.
        
        Args:
            team_id: NHL team ID
            
        Returns:
            List of imported players
        """
        logger.info(f"Importing roster for team {team_id}")
        
        # Get the team from the database
        db_team = self.db.query(Team).filter(Team.team_id == team_id).first()
        if not db_team:
            logger.error(f"Team {team_id} not found in database")
            return []
        
        # Fetch roster from NHL API
        roster_data = self.fetcher.get_team_roster(int(team_id))
        
        players = []
        for player_data in roster_data:
            person = player_data["person"]
            player_id = str(person["id"])
            position = player_data["position"]["code"]
            
            # Check if player already exists
            db_player = self.db.query(Player).filter(Player.player_id == player_id).first()
            
            if db_player:
                # Update existing player
                db_player.name = person["fullName"]
                db_player.team_id = db_team.id
                db_player.position = position
                logger.debug(f"Updated player: {db_player.name}")
            else:
                # Create new player
                db_player = Player(
                    player_id=player_id,
                    name=person["fullName"],
                    team_id=db_team.id,
                    position=position
                )
                self.db.add(db_player)
                logger.debug(f"Created player: {db_player.name}")
            
            players.append(db_player)
        
        self.db.commit()
        logger.info(f"Imported {len(players)} players for team {db_team.name}")
        return players
    
    def import_game(self, game_id: str, fetch_events: bool = True) -> Optional[Game]:
        """
        Import a specific NHL game.
        
        Args:
            game_id: NHL game ID
            fetch_events: Whether to fetch and import game events
            
        Returns:
            Created or updated game object
        """
        logger.info(f"Importing game {game_id}")
        
        # Fetch game data
        game_data = self.fetcher.get_game(int(game_id))
        if not game_data or "gameData" not in game_data:
            logger.error(f"Game {game_id} not found in NHL API")
            return None
        
        game_info = game_data["gameData"]
        
        # Get teams
        home_team_data = game_info["teams"]["home"]
        away_team_data = game_info["teams"]["away"]
        
        home_team = self.db.query(Team).filter(Team.team_id == str(home_team_data["id"])).first()
        away_team = self.db.query(Team).filter(Team.team_id == str(away_team_data["id"])).first()
        
        if not home_team or not away_team:
            logger.error(f"Teams for game {game_id} not found in database")
            return None
        
        # Game status info
        status = game_info["status"]["detailedState"]
        
        # Parse date
        date_str = game_info["datetime"]["dateTime"]
        date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        
        # Get season
        season = game_info["season"]
        
        # Get score if game is live or final
        home_score = 0
        away_score = 0
        period = 1
        time_remaining = "20:00"
        
        if "liveData" in game_data and "linescore" in game_data["liveData"]:
            linescore = game_data["liveData"]["linescore"]
            
            if "teams" in linescore:
                home_score = linescore["teams"]["home"].get("goals", 0)
                away_score = linescore["teams"]["away"].get("goals", 0)
            
            if "currentPeriod" in linescore:
                period = linescore["currentPeriod"]
            
            if "currentPeriodTimeRemaining" in linescore:
                time_remaining = linescore["currentPeriodTimeRemaining"]
        
        # Check if game already exists
        db_game = self.db.query(Game).filter(Game.game_id == game_id).first()
        
        if db_game:
            # Update existing game
            db_game.date = date
            db_game.season = season
            db_game.status = status
            db_game.period = period
            db_game.time_remaining = time_remaining
            db_game.home_score = home_score
            db_game.away_score = away_score
            logger.debug(f"Updated game: {db_game.game_id}")
        else:
            # Create new game
            db_game = Game(
                game_id=game_id,
                date=date,
                home_team_id=home_team.id,
                away_team_id=away_team.id,
                season=season,
                status=status,
                period=period,
                time_remaining=time_remaining,
                home_score=home_score,
                away_score=away_score
            )
            self.db.add(db_game)
            logger.debug(f"Created game: {db_game.game_id}")
        
        self.db.commit()
        self.db.refresh(db_game)
        
        # Import game events if requested
        if fetch_events:
            self.import_game_events(db_game, game_data)
        
        return db_game
    
    def import_game_events(self, db_game: Game, game_data: Dict[str, Any]) -> List[GameEvent]:
        """
        Import events for a game.
        
        Args:
            db_game: Game object
            game_data: Game data from NHL API
            
        Returns:
            List of created event objects
        """
        logger.info(f"Importing events for game {db_game.game_id}")
        
        if "liveData" not in game_data or "plays" not in game_data["liveData"]:
            logger.error(f"No play data found for game {db_game.game_id}")
            return []
        
        plays_data = game_data["liveData"]["plays"]
        all_plays = plays_data.get("allPlays", [])
        
        events = []
        for play in all_plays:
            # Process each play/event
            event = self.event_processor.process_event(db_game, play)
            if event:
                events.append(event)
        
        logger.info(f"Imported {len(events)} events for game {db_game.game_id}")
        return events
    
    def import_schedule(self, start_date: str, end_date: str, team_id: Optional[str] = None) -> List[Game]:
        """
        Import schedule for a date range.
        
        Args:
            start_date: Start date in format "YYYY-MM-DD"
            end_date: End date in format "YYYY-MM-DD"
            team_id: NHL team ID (optional)
            
        Returns:
            List of imported games
        """
        logger.info(f"Importing schedule from {start_date} to {end_date}")
        
        # Convert team_id to int if provided
        nhl_team_id = int(team_id) if team_id else None
        
        # Fetch schedule from NHL API
        schedule_data = self.fetcher.get_schedule(start_date, end_date, nhl_team_id)
        
        games = []
        for game_data in schedule_data:
            game_id = str(game_data["gamePk"])
            
            # Check if we need to fetch full game data
            status = game_data["status"]["detailedState"]
            if status in ["Final", "In Progress"]:
                # For completed or live games, import full data with events
                db_game = self.import_game(game_id, fetch_events=True)
            else:
                # For scheduled games, just create basic game entry
                db_game = self.import_basic_game(game_data)
            
            if db_game:
                games.append(db_game)
        
        logger.info(f"Imported {len(games)} games")
        return games
    
    def import_basic_game(self, game_data: Dict[str, Any]) -> Optional[Game]:
        """
        Import basic game info without events.
        
        Args:
            game_data: Game data from NHL API schedule
            
        Returns:
            Created or updated game object
        """
        game_id = str(game_data["gamePk"])
        
        # Get teams
        home_team_data = game_data["teams"]["home"]["team"]
        away_team_data = game_data["teams"]["away"]["team"]
        
        home_team = self.db.query(Team).filter(Team.team_id == str(home_team_data["id"])).first()
        away_team = self.db.query(Team).filter(Team.team_id == str(away_team_data["id"])).first()
        
        if not home_team or not away_team:
            logger.error(f"Teams for game {game_id} not found in database")
            return None
        
        # Parse date
        date_str = game_data["gameDate"]
        date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        
        # Get season
        season = game_data["season"]
        
        # Game status info
        status = game_data["status"]["detailedState"]
        
        # Score if available
        home_score = game_data["teams"]["home"].get("score", 0)
        away_score = game_data["teams"]["away"].get("score", 0)
        
        # Check if game already exists
        db_game = self.db.query(Game).filter(Game.game_id == game_id).first()
        
        if db_game:
            # Update existing game
            db_game.date = date
            db_game.season = season
            db_game.status = status
            db_game.home_score = home_score
            db_game.away_score = away_score
            logger.debug(f"Updated basic game: {db_game.game_id}")
        else:
            # Create new game
            db_game = Game(
                game_id=game_id,
                date=date,
                home_team_id=home_team.id,
                away_team_id=away_team.id,
                season=season,
                status=status,
                period=1,
                time_remaining="20:00",
                home_score=home_score,
                away_score=away_score
            )
            self.db.add(db_game)
            logger.debug(f"Created basic game: {db_game.game_id}")
        
        self.db.commit()
        self.db.refresh(db_game)
        return db_game
    
    def import_season(self, season: str, team_id: Optional[str] = None) -> List[Game]:
        """
        Import all games for a season.
        
        Args:
            season: Season in format "20222023"
            team_id: NHL team ID (optional)
            
        Returns:
            List of imported games
        """
        logger.info(f"Importing season {season}")
        
        # Parse season year
        year = int(season[:4])
        start_date = f"{year}-09-01"
        end_date = f"{year+1}-07-31"
        
        return self.import_schedule(start_date, end_date, team_id)