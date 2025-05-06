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
        self.base_url = "https://statsapi.web.nhl.com/api/v1"
        self.delay = 0.5  # Delay between API calls to avoid rate limiting
    
    def _get(self, endpoint: str) -> Dict[str, Any]:
        """
        Make a GET request to the NHL API.
        
        Args:
            endpoint: API endpoint to fetch
            
        Returns:
            Response data as dictionary
        """
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
    
    def get_teams(self) -> List[Dict[str, Any]]:
        """
        Get all NHL teams.
        
        Returns:
            List of team data
        """
        data = self._get("teams")
        return data.get("teams", [])
    
    def get_team(self, team_id: int) -> Dict[str, Any]:
        """
        Get details for a specific team.
        
        Args:
            team_id: NHL team ID
            
        Returns:
            Team data
        """
        data = self._get(f"teams/{team_id}")
        teams = data.get("teams", [])
        return teams[0] if teams else {}
    
    def get_team_roster(self, team_id: int) -> List[Dict[str, Any]]:
        """
        Get the current roster for a team.
        
        Args:
            team_id: NHL team ID
            
        Returns:
            List of players on the roster
        """
        data = self._get(f"teams/{team_id}/roster")
        return data.get("roster", [])
    
    def get_player(self, player_id: int) -> Dict[str, Any]:
        """
        Get detailed player information.
        
        Args:
            player_id: NHL player ID
            
        Returns:
            Player data
        """
        data = self._get(f"people/{player_id}")
        people = data.get("people", [])
        return people[0] if people else {}
    
    def get_player_stats(self, player_id: int, season: Optional[str] = None) -> Dict[str, Any]:
        """
        Get stats for a player.
        
        Args:
            player_id: NHL player ID
            season: Season in format "20222023" (optional)
            
        Returns:
            Player statistics
        """
        endpoint = f"people/{player_id}/stats?stats=statsSingleSeason"
        if season:
            endpoint += f"&season={season}"
        
        data = self._get(endpoint)
        stats = data.get("stats", [])
        return stats[0].get("splits", [{}])[0] if stats else {}
    
    def get_schedule(self, start_date: str, end_date: str, team_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get game schedule for a date range.
        
        Args:
            start_date: Start date in format "YYYY-MM-DD"
            end_date: End date in format "YYYY-MM-DD"
            team_id: NHL team ID (optional)
            
        Returns:
            List of scheduled games
        """
        endpoint = f"schedule?startDate={start_date}&endDate={end_date}"
        if team_id:
            endpoint += f"&teamId={team_id}"
        
        data = self._get(endpoint)
        dates = data.get("dates", [])
        
        games = []
        for date_info in dates:
            games.extend(date_info.get("games", []))
        
        return games
    
    def get_game(self, game_id: int) -> Dict[str, Any]:
        """
        Get detailed information for a specific game.
        
        Args:
            game_id: NHL game ID
            
        Returns:
            Game data
        """
        return self._get(f"game/{game_id}/feed/live")
    
    def get_game_boxscore(self, game_id: int) -> Dict[str, Any]:
        """
        Get boxscore information for a specific game.
        
        Args:
            game_id: NHL game ID
            
        Returns:
            Game boxscore data
        """
        data = self._get(f"game/{game_id}/boxscore")
        return data
    
    def get_game_shifts(self, game_id: int) -> List[Dict[str, Any]]:
        """
        Get shift data for a specific game.
        
        Args:
            game_id: NHL game ID
            
        Returns:
            Game shift data
        """
        # This endpoint uses a different base URL
        url = f"https://api.nhle.com/stats/rest/en/shiftcharts?cayenneExp=gameId={game_id}"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            time.sleep(self.delay)
            return response.json().get("data", [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching shifts for game {game_id}: {e}")
            return []
    
    def get_season_games(self, season: str, team_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get all games for a specific season.
        
        Args:
            season: Season in format "20222023"
            team_id: NHL team ID (optional)
            
        Returns:
            List of games
        """
        # Calculate season dates
        year = int(season[:4])
        start_date = f"{year}-09-01"
        end_date = f"{year+1}-07-31"
        
        return self.get_schedule(start_date, end_date, team_id)