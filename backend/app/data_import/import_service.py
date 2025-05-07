import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.base import Team, Player, GameEvent
from app.models.analytics import Game, PlayerTeamSeason
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
        Import NHL teams using the NHL Stats API.

        Returns:
            List[Team]: List of new teams imported
        """
        logger.info("Importing NHL teams")

        teams = self.fetcher.get_all_teams()
        team_metadata = self.fetcher.get_team_metadata()
        imported_teams = []

        for team in teams:
            team_id = team.get("id")
            if not team_id:
                continue
                
            # Convert team_id to string to match the database column type
            team_id = str(team_id)
                
            name = team.get("fullName")
            if not name:
                name = f"{team.get('locationName', '')} {team.get('teamName', '')}"
                
            abbreviation = team.get("triCode")
            if not abbreviation:
                abbreviation = team.get("abbreviation")
                
            franchise_id = team.get("franchiseId")
            if franchise_id:
                franchise_id = int(franchise_id)

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
                    division=meta.get("division", {}).get("name"),
                    conference=meta.get("conference", {}).get("name"),
                    city_name=team.get("locationName"),
                    team_name=team.get("teamName"),
                    venue_name=team.get("venue", {}).get("default"),
                    official_site_url=team.get("officialSiteUrl"),
                    active=True,
                )
                self.db.add(db_team)
                imported_teams.append(db_team)

        self.db.commit()
        logger.info(f"Imported {len(imported_teams)} teams")
        return imported_teams
    
    def import_team_roster(self, team_abbrev: str, season: Optional[str] = None) -> List[Player]:
        """
        Import roster for a specific team and season.
        
        Args:
            team_abbrev: NHL team abbreviation (e.g., "EDM")
            season: Season in format "20222023" (optional, defaults to current)
            
        Returns:
            List of imported players
        """
        logger.info(f"Importing roster for team {team_abbrev}{' for season ' + season if season else ''}")
        
        # Get the team from the database
        db_team = self.db.query(Team).filter(Team.abbreviation == team_abbrev).first()
        if not db_team:
            logger.error(f"Team {team_abbrev} not found in database")
            return []
        
        # Fetch roster from NHL API - either current or by season
        try:
            if season:
                roster_data = self.fetcher.get_team_roster_by_season(team_abbrev, season)
            else:
                roster_data = self.fetcher.get_team_roster(team_abbrev)
            
            # Check if we got valid data
            if not roster_data:
                logger.info(f"No roster data found for team {db_team.name}")
                return []
                
            # Extract all players from the different position groups
            all_players = []
            
            # Check if response has the correct format
            if isinstance(roster_data, dict):
                # Add players from each position group
                all_players.extend(roster_data.get("forwards", []))
                all_players.extend(roster_data.get("defensemen", []))
                all_players.extend(roster_data.get("goalies", []))
            elif isinstance(roster_data, list):
                # If it's already a list, use it directly
                all_players = roster_data
            
            players = []
            # Process all roster players
            for player_data in all_players:
                # Extract player information with the correct keys
                player_id = str(player_data["id"])
                
                # Get name from the nested structure
                first_name = player_data["firstName"]["default"] if isinstance(player_data["firstName"], dict) else player_data["firstName"]
                last_name = player_data["lastName"]["default"] if isinstance(player_data["lastName"], dict) else player_data["lastName"]
                name = f"{first_name} {last_name}"
                
                position = player_data["positionCode"]
                
                # Skip PlayerTeamSeason check until we have created the table
                # Check if player exists
                db_player = self.db.query(Player).filter(Player.player_id == player_id).first()
                
                # Get birth city with the correct structure
                birth_city = player_data.get("birthCity", {})
                if isinstance(birth_city, dict):
                    birth_city = birth_city.get("default", "")
                
                # Create or update player record
                if db_player:
                    # Update existing player
                    db_player.name = name
                    db_player.position = position
                    
                    # Update additional fields
                    db_player.sweater_number = player_data.get("sweaterNumber")
                    db_player.height_in_inches = player_data.get("heightInInches")
                    db_player.height_in_cm = player_data.get("heightInCentimeters")
                    db_player.weight_in_pounds = player_data.get("weightInPounds")
                    db_player.weight_in_kg = player_data.get("weightInKilograms")
                    
                    if "birthDate" in player_data:
                        db_player.birth_date = datetime.strptime(
                            player_data["birthDate"], "%Y-%m-%d"
                        ).date() if player_data["birthDate"] else None
                    
                    db_player.birth_city = birth_city
                    db_player.birth_country = player_data.get("birthCountry")
                    db_player.shoots_catches = player_data.get("shootsCatches")
                    db_player.headshot_url = player_data.get("headshot")
                    
                    logger.debug(f"Updated player: {db_player.name}")
                else:
                    # Create new player
                    db_player = Player(
                        player_id=player_id,
                        name=name,
                        position=position,
                        sweater_number=player_data.get("sweaterNumber"),
                        height_in_inches=player_data.get("heightInInches"),
                        height_in_cm=player_data.get("heightInCentimeters"),
                        weight_in_pounds=player_data.get("weightInPounds"),
                        weight_in_kg=player_data.get("weightInKilograms"),
                        birth_date=datetime.strptime(
                            player_data["birthDate"], "%Y-%m-%d"
                        ).date() if "birthDate" in player_data and player_data["birthDate"] else None,
                        birth_city=birth_city,
                        birth_country=player_data.get("birthCountry"),
                        shoots_catches=player_data.get("shootsCatches"),
                        headshot_url=player_data.get("headshot")
                    )
                    self.db.add(db_player)
                    logger.debug(f"Created player: {name}")
                
                # Skip PlayerTeamSeason stuff for now
                # For current roster, update the player's current team
                db_player.team_id = db_team.id
                
                players.append(db_player)
            
            self.db.commit()
            logger.info(f"Imported {len(players)} players for team {db_team.name}")
            return players
        
        except Exception as e:
            logger.error(f"Error importing roster for team {db_team.name}: {e}")
            return []
    
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
        # Get schedule for date range
        schedule_games = self.fetcher.get_schedule_range(start_date, end_date)
        
        # Add debug logging
        logger.info(f"Found {len(schedule_games)} games in schedule from {start_date} to {end_date}")
        
        if len(schedule_games) > 0:
            # Log a sample game to understand the structure
            import json
            sample_game = schedule_games[0]
            logger.debug(f"Sample game data structure: {json.dumps({k: sample_game[k] for k in list(sample_game.keys())[:5]}, indent=2)}")
        
        games = []
        for game_data in schedule_games:
            # Check if this is a game we want to import
            game_id = str(game_data.get("id"))
            
            # Filter by team if provided
            if team_abbrev:
                home_team = game_data.get("homeTeam", {}).get("abbrev")
                away_team = game_data.get("awayTeam", {}).get("abbrev")
                if team_abbrev not in [home_team, away_team]:
                    continue
            
            # Import completed or live games with events
            status = game_data.get("gameState", "")
            if status in ["FINAL", "LIVE"] and game_id:
                logger.info(f"Importing game {game_id}")
                db_game = self.import_game(game_id, fetch_events=True)
                if db_game:
                    games.append(db_game)
            else:
                # Import basic game info without events
                logger.info(f"Importing basic game {game_id} with status {status}")
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
            season: Season in format "20232024"
            team_abbrev: NHL team abbreviation (optional)
            
        Returns:
            List of imported games
        """
        logger.info(f"Importing season {season}")
        
        # Parse season year
        year = int(season[:4])
        
        # Get all teams if no specific team is provided
        if not team_abbrev:
            teams = self.db.query(Team).filter(Team.active == True).all()
            team_abbrevs = [team.abbreviation for team in teams]
        else:
            team_abbrevs = [team_abbrev]
        
        # Track all game IDs to avoid duplicates
        all_game_ids = set()
        imported_games = []
        
        # Define months we want to check (NHL season typically runs Oct-Jun)
        months = []
        for month in range(10, 13):  # Oct-Dec of start year
            months.append(f"{year}-{month:02d}")
        for month in range(1, 7):  # Jan-Jun of end year
            months.append(f"{year+1}-{month:02d}")
        
        # For each team, fetch their schedule for relevant months
        for team_abbr in team_abbrevs:
            logger.info(f"Fetching schedule for team {team_abbr}")
            
            for month in months:
                logger.info(f"Fetching {month} schedule for {team_abbr}")
                
                # Get the team's schedule for this month
                schedule_data = self.fetcher._get(f"/v1/club-schedule/{team_abbr}/month/{month}")
                
                if not schedule_data or "games" not in schedule_data:
                    logger.info(f"No games found for {team_abbr} in {month}")
                    continue
                    
                # Process games from this month
                month_games = schedule_data["games"]
                logger.info(f"Found {len(month_games)} games for {team_abbr} in {month}")
                
                # Import each game if we haven't already
                for game_data in month_games:
                    game_id = str(game_data.get("id"))
                    
                    # Skip if we've already processed this game
                    if game_id in all_game_ids:
                        continue
                        
                    all_game_ids.add(game_id)
                    
                    # Import the game with all its events
                    logger.info(f"Importing game {game_id}")
                    game = self.import_game(game_id, fetch_events=True)
                    if game:
                        imported_games.append(game)
        
        logger.info(f"Imported {len(imported_games)} games for season {season}")
        return imported_games