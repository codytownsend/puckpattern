import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.base import Team, Player, GameEvent
from app.models.analytics import Game
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
    
    def import_teams(self) -> int:
        """
        Import NHL teams using both static and live metadata sources.

        Returns:
            int: Number of new teams imported
        """
        logger.info("Importing NHL teams")

        teams = self.fetcher.get_all_teams()
        team_metadata = self.fetcher.get_team_metadata()
        imported_count = 0

        for team in teams:
            team_id = team["id"]
            name = team.get("fullName")
            abbreviation = team.get("triCode")
            franchise_id = team.get("franchiseId")

            # Skip placeholder teams
            if not name or "To be determined" in name or abbreviation == "NHL":
                continue

            meta = team_metadata.get(team_id, {})

            existing = self.db.query(Team).filter(Team.team_id == team_id).first()
            if not existing:
                db_team = Team(
                    team_id=team_id,
                    name=name,
                    abbreviation=abbreviation,
                    franchise_id=franchise_id,
                    division=meta.get("divisionName"),
                    conference=meta.get("conferenceName"),
                    city_name=meta.get("placeName", {}).get("default"),
                    venue_name=None,
                    official_site_url=None,
                    active=True,
                )
                self.db.add(db_team)
                imported_count += 1

        self.db.commit()
        logger.info(f"Imported {imported_count} teams")
        return imported_count
    
    def import_team_roster(self, team_abbrev: str) -> List[Player]:
        """
        Import roster for a specific team.
        
        Args:
            team_abbrev: NHL team abbreviation (e.g., "EDM")
            
        Returns:
            List of imported players
        """
        logger.info(f"Importing roster for team {team_abbrev}")
        
        # Get the team from the database
        db_team = self.db.query(Team).filter(Team.abbreviation == team_abbrev).first()
        if not db_team:
            logger.error(f"Team {team_abbrev} not found in database")
            return []
        
        # Fetch roster from NHL API
        roster_data = self.fetcher.get_team_roster(team_abbrev)
        
        players = []
        # Process all roster sections: forwards, defensemen, goalies
        for player_data in roster_data:
            player_id = str(player_data["playerId"])
            position = player_data["position"]
            
            # Check if player already exists
            db_player = self.db.query(Player).filter(Player.player_id == player_id).first()
            
            if db_player:
                # Update existing player
                db_player.name = player_data["playerName"]["default"]
                db_player.team_id = db_team.id
                db_player.position = position
                
                # Update additional fields
                db_player.player_slug = player_data.get("playerSlug")
                db_player.sweater_number = player_data.get("playerNum")
                db_player.height_in_inches = player_data.get("heightInInches")
                db_player.height_in_cm = player_data.get("heightInCentimeters")
                db_player.weight_in_pounds = player_data.get("weightInPounds")
                db_player.weight_in_kg = player_data.get("weightInKilograms")
                
                if "birthDate" in player_data:
                    db_player.birth_date = datetime.strptime(
                        player_data["birthDate"], "%Y-%m-%d"
                    ).date() if player_data["birthDate"] else None
                
                db_player.birth_city = player_data.get("birthCity", {}).get("default")
                db_player.birth_country = player_data.get("birthCountry")
                db_player.shoots_catches = player_data.get("shootsCatches")
                db_player.headshot_url = player_data.get("headshot")
                
                logger.debug(f"Updated player: {db_player.name}")
            else:
                # Create new player
                db_player = Player(
                    player_id=player_id,
                    name=player_data["playerName"]["default"],
                    team_id=db_team.id,
                    position=position,
                    player_slug=player_data.get("playerSlug"),
                    sweater_number=player_data.get("playerNum"),
                    height_in_inches=player_data.get("heightInInches"),
                    height_in_cm=player_data.get("heightInCentimeters"),
                    weight_in_pounds=player_data.get("weightInPounds"),
                    weight_in_kg=player_data.get("weightInKilograms"),
                    birth_date=datetime.strptime(
                        player_data["birthDate"], "%Y-%m-%d"
                    ).date() if "birthDate" in player_data and player_data["birthDate"] else None,
                    birth_city=player_data.get("birthCity", {}).get("default"),
                    birth_country=player_data.get("birthCountry"),
                    shoots_catches=player_data.get("shootsCatches"),
                    headshot_url=player_data.get("headshot")
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
        if not game_data:
            logger.error(f"Game {game_id} not found in NHL API")
            return None
        
        # Get teams
        home_team_data = game_data["homeTeam"]
        away_team_data = game_data["awayTeam"]
        
        home_team = self.db.query(Team).filter(Team.abbreviation == home_team_data["abbrev"]).first()
        away_team = self.db.query(Team).filter(Team.abbreviation == away_team_data["abbrev"]).first()
        
        if not home_team or not away_team:
            logger.error(f"Teams for game {game_id} not found in database")
            return None
        
        # Game status info
        status = game_data.get("gameState", "PREVIEW")
        
        # Parse date
        date_str = game_data["gameDate"]
        date = datetime.strptime(date_str, "%Y-%m-%d")
        
        # Get season
        season = game_data.get("season", str(date.year) + str(date.year + 1))
        
        # Get score
        home_score = home_team_data.get("score", 0)
        away_score = away_team_data.get("score", 0)
        
        # Get period info
        period = game_data.get("period", 1)
        time_remaining = game_data.get("clock", {}).get("timeRemaining", "20:00") if "clock" in game_data else "20:00"
        
        # Get venue
        venue = game_data.get("venue", {}).get("default", "")
        
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
            db_game.venue_name = venue
            db_game.game_type = game_data.get("gameType", 2)  # Default to regular season
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
                away_score=away_score,
                venue_name=venue,
                game_type=game_data.get("gameType", 2)  # Default to regular season
            )
            self.db.add(db_game)
            logger.debug(f"Created game: {db_game.game_id}")
        
        self.db.commit()
        self.db.refresh(db_game)
        
        # Import game events if requested
        if fetch_events:
            self.import_game_events(db_game)
        
        return db_game
    
    def import_game_events(self, db_game: Game) -> List[GameEvent]:
        """
        Import events for a game.
        
        Args:
            db_game: Game object
            
        Returns:
            List of created event objects
        """
        logger.info(f"Importing events for game {db_game.game_id}")
        
        # Fetch play-by-play data from NHL API
        play_by_play_data = self.fetcher.get_game_play_by_play(int(db_game.game_id))
        
        if not play_by_play_data or "plays" not in play_by_play_data:
            logger.error(f"No play data found for game {db_game.game_id}")
            return []
        
        plays = play_by_play_data["plays"]
        
        events = []
        for play in plays:
            # Process each play/event
            event = self.event_processor.process_event(db_game, play)
            if event:
                events.append(event)
        
        logger.info(f"Imported {len(events)} events for game {db_game.game_id}")
        return events
    
    def import_schedule(self, start_date: str, end_date: str, team_abbrev: Optional[str] = None) -> List[Game]:
        """
        Import schedule for a date range.
        
        Args:
            start_date: Start date in format "YYYY-MM-DD"
            end_date: End date in format "YYYY-MM-DD"
            team_abbrev: NHL team abbreviation (optional)
            
        Returns:
            List of imported games
        """
        logger.info(f"Importing schedule from {start_date} to {end_date}")
        
        # Fetch schedule data
        schedule_games = self.fetcher.get_schedule_range(start_date, end_date)
        games: List[Game] = []
        for game_data in schedule_games:
            game_id = str(game_data["id"])
            status = game_data.get("gameState", "PREVIEW")
            # Completed or live => import full with events
            if status in ["FINAL", "LIVE"]:
                db_game = self.import_game(game_id, fetch_events=True)
            else:
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
        game_id = str(game_data["id"])
        
        # Get teams
        home_team_data = game_data["homeTeam"]
        away_team_data = game_data["awayTeam"]
        
        home_team = self.db.query(Team).filter(Team.abbreviation == home_team_data["abbrev"]).first()
        away_team = self.db.query(Team).filter(Team.abbreviation == away_team_data["abbrev"]).first()
        
        if not home_team or not away_team:
            logger.error(f"Teams for game {game_id} not found in database")
            return None
        
        # Parse date
        date_str = game_data["gameDate"]
        date = datetime.strptime(date_str, "%Y-%m-%d")
        
        # Get season
        season = game_data.get("season", str(date.year) + str(date.year + 1))
        
        # Game status info
        status = game_data.get("gameState", "PREVIEW")
        
        # Score if available
        home_score = home_team_data.get("score", 0)
        away_score = away_team_data.get("score", 0)
        
        # Venue if available
        venue = game_data.get("venue", {}).get("default", "")
        
        # Game type
        game_type = game_data.get("gameType", 2)  # Default to regular season
        
        # Check if game already exists
        db_game = self.db.query(Game).filter(Game.game_id == game_id).first()
        
        if db_game:
            # Update existing game
            db_game.date = date
            db_game.season = season
            db_game.status = status
            db_game.home_score = home_score
            db_game.away_score = away_score
            db_game.venue_name = venue
            db_game.game_type = game_type
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
                away_score=away_score,
                venue_name=venue,
                game_type=game_type
            )
            self.db.add(db_game)
            logger.debug(f"Created basic game: {db_game.game_id}")
        
        self.db.commit()
        self.db.refresh(db_game)
        return db_game
    
    def import_season(self, season: str, team_abbrev: Optional[str] = None) -> List[Game]:
        """
        Import all games for a season.
        
        Args:
            season: Season in format "20222023"
            team_abbrev: NHL team abbreviation (optional)
            
        Returns:
            List of imported games
        """
        logger.info(f"Importing season {season}")
        
        # Parse season year
        year = int(season[:4])
        start_date = f"{year}-09-01"
        end_date = f"{year+1}-07-31"
        
        return self.import_schedule(start_date, end_date, team_abbrev)