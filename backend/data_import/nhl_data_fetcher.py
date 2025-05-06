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
        self.base_url = "https://api-web.nhle.com/v1"
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
        data = self._get("meta?teams=all")
        return data.get("teams", [])
    
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
    
    def get_schedule(self, date: str) -> Dict[str, Any]:
        """
        Get game schedule for a specific date.
        
        Args:
            date: Date in format "YYYY-MM-DD"
            
        Returns:
            List of scheduled games
        """
        return self._get(f"schedule/{date}")
    
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
        return self._get(f"gamecenter/{game_id}/landing")
    
    def get_game_boxscore(self, game_id: int) -> Dict[str, Any]:
        """
        Get boxscore information for a specific game.
        
        Args:
            game_id: NHL game ID
            
        Returns:
            Game boxscore data
        """
        return self._get(f"gamecenter/{game_id}/boxscore")
    
    def get_game_play_by_play(self, game_id: int) -> Dict[str, Any]:
        """
        Get play-by-play data for a specific game.
        
        Args:
            game_id: NHL game ID
            
        Returns:
            Play-by-play data
        """
        return self._get(f"gamecenter/{game_id}/play-by-play")
    
    def get_standings(self) -> Dict[str, Any]:
        """
        Get current standings.
        
        Returns:
            Standings data
        """
        return self._get("standings/now")
    
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
    
    def get_club_stats(self, team_abbrev: str) -> Dict[str, Any]:
        """
        Get statistics for a specific club.
        
        Args:
            team_abbrev: NHL team abbreviation (e.g., "EDM")
            
        Returns:
            Club statistics data
        """
        return self._get(f"club-stats/{team_abbrev}/now")