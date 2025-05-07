import requests
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class NHLDataFetcher:
    """
    Service for fetching data from the NHL API.
    """
    
    def __init__(self):
        self.base_url = "https://api.nhle.com/stats/rest"
        self.web_url = "https://api-web.nhle.com/v1"
        self.delay = 0.5  # Delay between API calls to avoid rate limiting
    
    def _get(self, endpoint: str) -> Dict[str, Any]:
        """
        Make a GET request to the NHL API.
                
        Returns:
            Response data as dictionary
        """
        # Determine if this is a web API or stats API endpoint
        if endpoint.startswith('http'):
            url = endpoint
        elif endpoint.startswith('/v1'):
            url = f"https://api-web.nhle.com{endpoint}"
        else:
            url = f"{self.base_url}/{endpoint}"
            
        logger.debug(f"Fetching NHL API: {url}")
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            time.sleep(self.delay)  # Add delay to avoid rate limiting
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return {}
    
    def get_all_teams(self) -> List[Dict[str, Any]]:
        """
        Returns all teams from the NHL Stats API.
        """
        data = self._get("en/team")
        
        # Check if we got a valid response with teams
        if not data or "data" not in data:
            return []
        
        return data.get("data", [])

    def get_team_metadata(self) -> Dict[int, Dict[str, Any]]:
        """
        Returns a mapping of team_id → metadata.
        """
        data = self._get("en/team")
        
        if not data or "data" not in data:
            return {}
        
        # Create a dictionary mapping team IDs to their full data
        team_data = {}
        for team in data.get("data", []):
            if "id" in team:
                team_data[team["id"]] = team
        
        return team_data
    
    def get_team(self, team_abbrev: str) -> Dict[str, Any]:
        """
        Get details for a specific team.
        
        Args:
            team_abbrev: NHL team abbreviation (e.g., "EDM")
            
        Returns:
            Team data
        """
        data = self._get(f"meta?teams={team_abbrev}")
        teams = data.get("teams", [])
        return teams[0] if teams else {}
    
    def get_team_roster(self, team_abbrev: str) -> List[Dict[str, Any]]:
        """
        Get the current roster for a team.
        
        Args:
            team_abbrev: NHL team abbreviation (e.g., "EDM")
            
        Returns:
            List of players on the roster
        """
        data = self._get(f"roster/{team_abbrev}/current")
        # Combine forwards, defensemen, and goalies into one list
        players = []
        players.extend(data.get("forwards", []))
        players.extend(data.get("defensemen", []))
        players.extend(data.get("goalies", []))
        return players
    
    def get_team_roster_by_season(self, team_abbrev: str, season: str) -> Dict[str, Any]:
        """
        Get the roster for a team by season.
        
        Args:
            team_abbrev: NHL team abbreviation (e.g., "EDM")
            season: Season in format "20232024"
            
        Returns:
            Dictionary containing forwards, defensemen, and goalies lists
        """
        # Directly use the web API endpoint structure
        data = self._get(f"/v1/roster/{team_abbrev}/{season}")
        
        return data or {}  # Return empty dict if no data
    
    def get_player(self, player_id: int) -> Dict[str, Any]:
        """
        Get detailed player information.
        
        Args:
            player_id: NHL player ID
            
        Returns:
            Player data
        """
        data = self._get(f"player/{player_id}/landing")
        return data if data else {}
    
    def get_player_stats(self, player_id: int, season: Optional[str] = None, game_type: int = 2) -> Dict[str, Any]:
        """
        Get stats for a player.
        
        Args:
            player_id: NHL player ID
            season: Season in format "20232024" (optional)
            game_type: Game type (2 for regular season, 3 for playoffs)
            
        Returns:
            Player statistics
        """
        if season:
            endpoint = f"player/{player_id}/game-log/{season}/{game_type}"
        else:
            endpoint = f"player/{player_id}/game-log/now"
        
        return self._get(endpoint)
    
    def get_schedule(self, date: str) -> List[Dict[str, Any]]:
        """
        Get game schedule for a specific date.

        Args:
            date (str): Date in format "YYYY-MM-DD"

        Returns:
            List[Dict[str, Any]]: List of game dictionaries for the specified date
        """
        # Try the web API format first
        data = self._get(f"/v1/schedule/{date}")
        
        # Check response structure
        if not data:
            # Try alternative endpoint format
            data = self._get(f"/v1/scoreboard/{date}")
        
        # Process the response
        games = []
        
        # Handle different response formats
        if data and "games" in data:
            games = data["games"]
        elif data and "gameWeek" in data:
            for day in data["gameWeek"]:
                if "date" in day and day["date"] == date and "games" in day:
                    games.extend(day["games"])
        
        return games
    
    def get_team_month_schedule(self, team_abbrev: str, month: str) -> Dict[str, Any]:
        """
        Get schedule for a team for a specific month.
        
        Args:
            team_abbrev: NHL team abbreviation (e.g., "TOR")
            month: Month in format "YYYY-MM"
            
        Returns:
            Schedule data
        """
        return self._get(f"/v1/club-schedule/{team_abbrev}/month/{month}")

    def get_schedule_range(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        Get game schedule for a date range by iterating over dates.

        Args:
            start_date (str): Start date in format "YYYY-MM-DD"
            end_date (str): End date in format "YYYY-MM-DD"

        Returns:
            List[Dict[str, Any]]: Flat list of game dictionaries across the date range
        """
        from datetime import datetime, timedelta

        all_games: List[Dict[str, Any]] = []
        current = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        while current <= end:
            date_str = current.strftime("%Y-%m-%d")
            games = self.get_schedule(date_str)
            all_games.extend(games)
            current += timedelta(days=1)

        return all_games
    
    def get_current_schedule(self) -> Dict[str, Any]:
        """
        Get current schedule.
        
        Returns:
            Current schedule data
        """
        return self._get("schedule/now")
    
    def get_schedule_calendar(self, date: Optional[str] = None) -> Dict[str, Any]:
        """
        Get schedule calendar.
        
        Args:
            date: Date in format "YYYY-MM-DD" (optional)
            
        Returns:
            Schedule calendar data
        """
        if date:
            return self._get(f"schedule-calendar/{date}")
        else:
            return self._get("schedule-calendar/now")
    
    def get_team_schedule(self, team_abbrev: str, month: Optional[str] = None) -> Dict[str, Any]:
        """
        Get schedule for a specific team and month.
        
        Args:
            team_abbrev: NHL team abbreviation (e.g., "EDM")
            month: Month in format "YYYY-MM" (optional, defaults to current month)
            
        Returns:
            Team schedule data
        """
        if month:
            return self._get(f"club-schedule/{team_abbrev}/month/{month}")
        else:
            return self._get(f"club-schedule/{team_abbrev}/month/now")
    
    def get_team_week_schedule(self, team_abbrev: str, date: Optional[str] = None) -> Dict[str, Any]:
        """
        Get weekly schedule for a specific team.
        
        Args:
            team_abbrev: NHL team abbreviation (e.g., "EDM")
            date: Date in format "YYYY-MM-DD" (optional, defaults to current week)
            
        Returns:
            Team weekly schedule data
        """
        if date:
            return self._get(f"club-schedule/{team_abbrev}/week/{date}")
        else:
            return self._get(f"club-schedule/{team_abbrev}/week/now")
    
    def get_team_season_schedule(self, team_abbrev: str, season: Optional[str] = None) -> Dict[str, Any]:
        """
        Get season schedule for a specific team.
        
        Args:
            team_abbrev: NHL team abbreviation (e.g., "EDM")
            season: Season in format "20232024" (optional)
            
        Returns:
            Team season schedule data
        """
        if season:
            return self._get(f"club-schedule-season/{team_abbrev}/{season}")
        else:
            return self._get(f"club-schedule-season/{team_abbrev}/now")
    
    def get_game(self, game_id: int) -> Dict[str, Any]:
        """
        Get detailed information for a specific game.
        
        Args:
            game_id: NHL game ID
            
        Returns:
            Game data
        """
        return self._get(f"/v1/gamecenter/{game_id}/landing")
    
    def get_game_boxscore(self, game_id: int) -> Dict[str, Any]:
        """
        Get boxscore information for a specific game.
        
        Args:
            game_id: NHL game ID
            
        Returns:
            Game boxscore data
        """
        return self._get(f"/v1/gamecenter/{game_id}/boxscore")
    
    def get_game_play_by_play(self, game_id: int) -> Dict[str, Any]:
        """
        Get play-by-play data for a specific game.
        
        Args:
            game_id: NHL game ID
            
        Returns:
            Play-by-play data
        """
        return self._get(f"/v1/gamecenter/{game_id}/play-by-play")
    
    def get_game_right_rail(self, game_id: int) -> Dict[str, Any]:
        """
        Get right rail content for a specific game.
        
        Args:
            game_id: NHL game ID
            
        Returns:
            Game right rail content
        """
        return self._get(f"gamecenter/{game_id}/right-rail")
    
    def get_game_story(self, game_id: int) -> Dict[str, Any]:
        """
        Get game story for a specific game.
        
        Args:
            game_id: NHL game ID
            
        Returns:
            Game story data
        """
        return self._get(f"wsc/game-story/{game_id}")
    
    def get_standings(self) -> Dict[str, Any]:
        """
        Get current standings.
        
        Returns:
            Standings data
        """
        return self._get("standings/now")
    
    def get_standings_by_date(self, date: str) -> Dict[str, Any]:
        """
        Get standings for a specific date.
        
        Args:
            date: Date in format "YYYY-MM-DD"
            
        Returns:
            Standings data
        """
        return self._get(f"standings/{date}")
    
    def get_standings_season(self) -> Dict[str, Any]:
        """
        Get standings season information.
        
        Returns:
            Standings season data
        """
        return self._get("standings-season")
    
    def get_scoreboard(self) -> Dict[str, Any]:
        """
        Get current scoreboard.
        
        Returns:
            Scoreboard data
        """
        return self._get("scoreboard/now")
    
    def get_daily_scores(self, date: Optional[str] = None) -> Dict[str, Any]:
        """
        Get daily scores for a specific date.
        
        Args:
            date: Date in format "YYYY-MM-DD" (optional, defaults to current date)
            
        Returns:
            Daily scores data
        """
        if date:
            return self._get(f"score/{date}")
        else:
            return self._get("score/now")
    
    def get_skater_stats_leaders(self, categories: str = "goals,assists,points", limit: int = 10) -> Dict[str, Any]:
        """
        Get current skater stats leaders.
        
        Args:
            categories: Statistical categories (comma-separated)
            limit: Number of players to return per category
            
        Returns:
            Skater stats leaders data
        """
        return self._get(f"skater-stats-leaders/current?categories={categories}&limit={limit}")
    
    def get_skater_stats_leaders_by_season(self, season: str, game_type: int, 
                                         categories: str = "goals,assists,points", limit: int = 10) -> Dict[str, Any]:
        """
        Get skater stats leaders for a specific season and game type.
        
        Args:
            season: Season in format "20232024"
            game_type: Game type (2 for regular season, 3 for playoffs)
            categories: Statistical categories (comma-separated)
            limit: Number of players to return per category
            
        Returns:
            Skater stats leaders data
        """
        return self._get(f"skater-stats-leaders/{season}/{game_type}?categories={categories}&limit={limit}")
    
    def get_goalie_stats_leaders(self, categories: str = "wins,gaa,savePct", limit: int = 10) -> Dict[str, Any]:
        """
        Get current goalie stats leaders.
        
        Args:
            categories: Statistical categories (comma-separated)
            limit: Number of goalies to return per category
            
        Returns:
            Goalie stats leaders data
        """
        return self._get(f"goalie-stats-leaders/current?categories={categories}&limit={limit}")
    
    def get_goalie_stats_leaders_by_season(self, season: str, game_type: int,
                                        categories: str = "wins,gaa,savePct", limit: int = 10) -> Dict[str, Any]:
        """
        Get goalie stats leaders for a specific season and game type.
        
        Args:
            season: Season in format "20232024"
            game_type: Game type (2 for regular season, 3 for playoffs)
            categories: Statistical categories (comma-separated)
            limit: Number of goalies to return per category
            
        Returns:
            Goalie stats leaders data
        """
        return self._get(f"goalie-stats-leaders/{season}/{game_type}?categories={categories}&limit={limit}")
    
    def get_club_stats(self, team_abbrev: str) -> Dict[str, Any]:
        """
        Get statistics for a specific club.
        
        Args:
            team_abbrev: NHL team abbreviation (e.g., "EDM")
            
        Returns:
            Club statistics data
        """
        return self._get(f"club-stats/{team_abbrev}/now")
    
    def get_club_stats_by_season(self, team_abbrev: str, season: str, game_type: int) -> Dict[str, Any]:
        """
        Get statistics for a specific club, season, and game type.
        
        Args:
            team_abbrev: NHL team abbreviation (e.g., "EDM")
            season: Season in format "20232024"
            game_type: Game type (2 for regular season, 3 for playoffs)
            
        Returns:
            Club statistics data
        """
        return self._get(f"club-stats/{team_abbrev}/{season}/{game_type}")
    
    def get_club_stats_season(self, team_abbrev: str) -> Dict[str, Any]:
        """
        Get club stats season information.
        
        Args:
            team_abbrev: NHL team abbreviation (e.g., "EDM")
            
        Returns:
            Club stats season data
        """
        return self._get(f"club-stats-season/{team_abbrev}")
    
    def get_tv_schedule(self, date: Optional[str] = None) -> Dict[str, Any]:
        """
        Get TV schedule for a specific date.
        
        Args:
            date: Date in format "YYYY-MM-DD" (optional, defaults to current date)
            
        Returns:
            TV schedule data
        """
        if date:
            return self._get(f"network/tv-schedule/{date}")
        else:
            return self._get("network/tv-schedule/now")
    
    def get_streams(self) -> Dict[str, Any]:
        """
        Get information about streaming options.
        
        Returns:
            Streaming options data
        """
        return self._get("where-to-watch")
    
    def get_playoff_series_carousel(self, season: str) -> Dict[str, Any]:
        """
        Get playoff series carousel for a specific season.
        
        Args:
            season: Season in format "20232024"
            
        Returns:
            Playoff series carousel data
        """
        return self._get(f"playoff-series/carousel/{season}/")
    
    def get_playoff_series_schedule(self, season: str, series_letter: str) -> Dict[str, Any]:
        """
        Get schedule for a specific playoff series.
        
        Args:
            season: Season in format "20232024"
            series_letter: Single letter indicating which series to retrieve
            
        Returns:
            Playoff series schedule data
        """
        return self._get(f"schedule/playoff-series/{season}/{series_letter}/")
    
    def get_playoff_bracket(self, year: str) -> Dict[str, Any]:
        """
        Get the playoff bracket for a specific year.
        
        Args:
            year: Year in YYYY format
            
        Returns:
            Playoff bracket data
        """
        return self._get(f"playoff-bracket/{year}")
    
    def get_seasons(self) -> Dict[str, Any]:
        """
        Get list of all NHL seasons.
        
        Returns:
            Seasons data
        """
        return self._get("season")
    
    def get_draft_rankings(self, category: Optional[int] = None) -> Dict[str, Any]:
        """
        Get current draft rankings.
        
        Args:
            category: Prospect category (1-4, optional)
            
        Returns:
            Draft rankings data
        """
        if category:
            # For specific category
            return self._get(f"draft/rankings/now?category={category}")
        else:
            # For all categories
            return self._get("draft/rankings/now")
    
    def get_draft_rankings_by_season(self, season: str, category: int) -> Dict[str, Any]:
        """
        Get draft rankings for a specific season and prospect category.
        
        Args:
            season: Season in YYYY format
            category: Prospect Category (1-4)
            
        Returns:
            Draft rankings data
        """
        return self._get(f"draft/rankings/{season}/{category}")
    
    def get_draft_tracker(self) -> Dict[str, Any]:
        """
        Get current draft tracker information.
        
        Returns:
            Draft tracker data
        """
        return self._get("draft-tracker/picks/now")
    
    def get_draft_picks(self, season: str, round_num: str) -> Dict[str, Any]:
        """
        Get draft picks for a specific season and round.
        
        Args:
            season: Season in YYYY format
            round_num: Round number (1-7) or "all" for all rounds
            
        Returns:
            Draft picks data
        """
        return self._get(f"draft/picks/{season}/{round_num}")
    
    def get_current_draft_picks(self) -> Dict[str, Any]:
        """
        Get current draft picks information.
        
        Returns:
            Current draft picks data
        """
        return self._get("draft/picks/now")
    
    def get_player_spotlight(self) -> Dict[str, Any]:
        """
        Get information about players in the spotlight.
        
        Returns:
            Player spotlight data
        """
        return self._get("player-spotlight")
    
    def get_meta(self, players: Optional[str] = None, teams: Optional[str] = None) -> Dict[str, Any]:
        """
        Get meta information.
        
        Args:
            players: Player IDs (comma-separated, optional)
            teams: Team codes (comma-separated, optional)
            
        Returns:
            Meta information data
        """
        params = []
        
        if players:
            params.append(f"players={players}")
        
        if teams:
            params.append(f"teams={teams}")
        
        query_string = "&".join(params)
        
        if query_string:
            return self._get(f"meta?{query_string}")
        else:
            return self._get("meta")
    
    def get_meta_game(self, game_id: int) -> Dict[str, Any]:
        """
        Get meta information for a specific game.
        
        Args:
            game_id: NHL game ID
            
        Returns:
            Game meta information
        """
        return self._get(f"meta/game/{game_id}")
    
    def get_location(self) -> Dict[str, Any]:
        """
        Get location information.
        
        Returns:
            Location data
        """
        return self._get("location")
    
    def get_playoff_series_meta(self, year: str, series_letter: str) -> Dict[str, Any]:
        """
        Get meta information for a specific playoff series.
        
        Args:
            year: Year in YYYY format
            series_letter: Single letter indicating which series
            
        Returns:
            Playoff series meta information
        """
        return self._get(f"meta/playoff-series/{year}/{series_letter}")
    
    def get_postal_lookup(self, postal_code: str) -> Dict[str, Any]:
        """
        Get information based on postal code.
        
        Args:
            postal_code: Postal (or zip) code
            
        Returns:
            Postal code information
        """
        return self._get(f"postal-lookup/{postal_code}")
    
    def get_goal_replay(self, game_id: int, event_number: int) -> Dict[str, Any]:
        """
        Get goal replay information.
        
        Args:
            game_id: NHL game ID
            event_number: Event number within the game
            
        Returns:
            Goal replay information
        """
        return self._get(f"ppt-replay/goal/{game_id}/{event_number}")
    
    def get_play_replay(self, game_id: int, event_number: int) -> Dict[str, Any]:
        """
        Get play replay information.
        
        Args:
            game_id: NHL game ID
            event_number: Event number within the game
            
        Returns:
            Play replay information
        """
        return self._get(f"ppt-replay/{game_id}/{event_number}")
    
    def get_wsc_play_by_play(self, game_id: int) -> Dict[str, Any]:
        """
        Get WSC play-by-play information.
        
        Args:
            game_id: NHL game ID
            
        Returns:
            WSC play-by-play information
        """
        return self._get(f"wsc/play-by-play/{game_id}")