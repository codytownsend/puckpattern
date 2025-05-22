"""
NHL API Data Collector - Phase 1
Collects teams, players, and basic stats from NHL API
"""
import requests
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models import Team, Player, Season, TeamRoster, PlayerSeasonStats, TeamSeasonStats

logger = logging.getLogger(__name__)

class NHLDataCollector:
    """Collects data from NHL API and stores in our simplified schema"""
    
    def __init__(self, db: Session):
        self.db = db
        self.base_url = "https://api-web.nhle.com/v1"
        self.session = requests.Session()
        
    def collect_season_data(self, season_id: str) -> Dict[str, int]:
        """
        Collect all data for a season
        
        Args:
            season_id: Season like "2023-24"
            
        Returns:
            Dictionary with counts of collected items
        """
        logger.info(f"Starting data collection for season {season_id}")
        stats = {
            "teams": 0,
            "players": 0, 
            "roster_entries": 0,
            "player_stats": 0,
            "team_stats": 0
        }
        
        try:
            # 1. Ensure season exists
            self._create_season(season_id)
            
            # 2. Collect teams
            stats["teams"] = self._collect_teams()
            
            # 3. Collect team rosters and player info
            teams = self.db.query(Team).all()
            for team in teams:
                roster_count, player_count = self._collect_team_roster(team.team_id, season_id)
                stats["roster_entries"] += roster_count
                stats["players"] += player_count
            
            # 4. Collect team stats
            stats["team_stats"] = self._collect_team_stats(season_id)
            
            # 5. Collect player stats
            stats["player_stats"] = self._collect_player_stats(season_id)
            
            self.db.commit()
            logger.info(f"Data collection complete: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error collecting season data: {e}")
            self.db.rollback()
            raise
    
    def _create_season(self, season_id: str) -> Season:
        """Create or get season record"""
        season = self.db.query(Season).filter(Season.season_id == season_id).first()
        if not season:
            # Parse season dates (simplified)
            start_year = int(season_id.split('-')[0])
            season = Season(
                season_id=season_id,
                start_date=date(start_year, 10, 1),  # Season starts ~Oct 1
                end_date=date(start_year + 1, 6, 30),  # Ends ~June 30
                is_current=(season_id == "2024-25")  # Adjust as needed
            )
            self.db.add(season)
            self.db.flush()
        return season
    
    def _collect_teams(self) -> int:
        """Collect all NHL teams"""
        logger.info("Collecting teams...")
        
        try:
            # Get team data from NHL API
            response = self.session.get(f"{self.base_url}/standings/2025-04-17")
            response.raise_for_status()
            data = response.json()
            
            teams_added = 0
            
            # Extract teams from standings
            for standing in data.get("standings", []):
                team_data = standing.get("teamAbbrev", {})
                if not team_data:
                    continue
                    
                team_id = str(standing.get("teamId", ""))
                if not team_id:
                    continue
                
                # Check if team exists
                existing_team = self.db.query(Team).filter(Team.team_id == team_id).first()
                if existing_team:
                    continue
                
                # Create new team
                team = Team(
                    team_id=team_id,
                    name=standing.get("teamName", {}).get("default", ""),
                    abbreviation=team_data.get("default", ""),
                    city=standing.get("placeName", {}).get("default", ""),
                    conference=standing.get("conferenceName", ""),
                    division=standing.get("divisionName", "")
                )
                
                self.db.add(team)
                teams_added += 1
            
            self.db.flush()
            logger.info(f"Added {teams_added} teams")
            return teams_added
            
        except Exception as e:
            logger.error(f"Error collecting teams: {e}")
            return 0
    
    def _collect_team_roster(self, team_id: str, season_id: str) -> tuple[int, int]:
        """
        Collect roster for a specific team and season
        
        Returns:
            (roster_entries_added, new_players_added)
        """
        logger.info(f"Collecting roster for team {team_id}, season {season_id}")
        
        try:
            # Get roster from NHL API
            response = self.session.get(f"{self.base_url}/roster/{team_id}/{season_id.replace('-', '')}")
            response.raise_for_status()
            data = response.json()
            
            roster_entries = 0
            new_players = 0
            
            # Process forwards, defensemen, and goalies
            for position_group in ["forwards", "defensemen", "goalies"]:
                players = data.get(position_group, [])
                
                for player_data in players:
                    player_id = str(player_data.get("id", ""))
                    if not player_id:
                        continue
                    
                    # Create/update player
                    if self._create_or_update_player(player_data):
                        new_players += 1
                    
                    # Add to roster
                    if self._add_to_roster(team_id, player_id, season_id, player_data):
                        roster_entries += 1
            
            logger.info(f"Added {roster_entries} roster entries, {new_players} new players for {team_id}")
            return roster_entries, new_players
            
        except Exception as e:
            logger.error(f"Error collecting roster for {team_id}: {e}")
            return 0, 0
    
    def _create_or_update_player(self, player_data: Dict) -> bool:
        """Create or update player record"""
        player_id = str(player_data.get("id", ""))
        
        existing_player = self.db.query(Player).filter(Player.player_id == player_id).first()
        if existing_player:
            return False  # Player already exists
        
        # Parse birth date
        birth_date = None
        if player_data.get("birthDate"):
            try:
                birth_date = datetime.strptime(player_data["birthDate"], "%Y-%m-%d").date()
            except:
                pass
        
        player = Player(
            player_id=player_id,
            name=f"{player_data.get('firstName', {}).get('default', '')} {player_data.get('lastName', {}).get('default', '')}".strip(),
            position=player_data.get("positionCode", ""),
            birth_date=birth_date,
            birth_city=player_data.get("birthCity", {}).get("default", ""),
            birth_country=player_data.get("birthCountry", ""),
            height_inches=player_data.get("heightInInches"),
            weight_pounds=player_data.get("weightInPounds"),
            shoots_catches=player_data.get("shootsCatches", "")
        )
        
        self.db.add(player)
        return True
    
    def _add_to_roster(self, team_id: str, player_id: str, season_id: str, player_data: Dict) -> bool:
        """Add player to team roster"""
        # Check if already exists
        existing = self.db.query(TeamRoster).filter(
            TeamRoster.team_id == team_id,
            TeamRoster.player_id == player_id,
            TeamRoster.season_id == season_id
        ).first()
        
        if existing:
            return False
        
        roster_entry = TeamRoster(
            team_id=team_id,
            player_id=player_id,
            season_id=season_id,
            jersey_number=str(player_data.get("sweaterNumber", "")),
            position=player_data.get("positionCode", "")
        )
        
        self.db.add(roster_entry)
        return True
    
    def _collect_team_stats(self, season_id: str) -> int:
        """Collect team statistics for the season"""
        logger.info(f"Collecting team stats for {season_id}")
        
        try:
            response = self.session.get(f"{self.base_url}/standings/{season_id.replace('-', '')}")
            response.raise_for_status()
            data = response.json()
            
            stats_added = 0
            
            for standing in data.get("standings", []):
                team_id = str(standing.get("teamId", ""))
                if not team_id:
                    continue
                
                # Check if stats already exist
                existing = self.db.query(TeamSeasonStats).filter(
                    TeamSeasonStats.team_id == team_id,
                    TeamSeasonStats.season_id == season_id
                ).first()
                
                if existing:
                    continue
                
                # Create team stats
                team_stats = TeamSeasonStats(
                    team_id=team_id,
                    season_id=season_id,
                    games_played=standing.get("gamesPlayed", 0),
                    wins=standing.get("wins", 0),
                    losses=standing.get("losses", 0),
                    overtime_losses=standing.get("otLosses", 0),
                    points=standing.get("points", 0),
                    goals_for=standing.get("goalFor", 0),
                    goals_against=standing.get("goalAgainst", 0),
                    goals_per_game=standing.get("goalFor", 0) / max(1, standing.get("gamesPlayed", 1)),
                    goals_against_per_game=standing.get("goalAgainst", 0) / max(1, standing.get("gamesPlayed", 1))
                )
                
                self.db.add(team_stats)
                stats_added += 1
            
            logger.info(f"Added {stats_added} team stat records")
            return stats_added
            
        except Exception as e:
            logger.error(f"Error collecting team stats: {e}")
            return 0
    
    def _collect_player_stats(self, season_id: str) -> int:
        """Collect player statistics for the season"""
        logger.info(f"Collecting player stats for {season_id}")
        
        stats_added = 0
        
        # Get all roster entries for this season
        roster_entries = self.db.query(TeamRoster).filter(
            TeamRoster.season_id == season_id
        ).all()
        
        for roster_entry in roster_entries:
            try:
                # Get player stats from NHL API
                response = self.session.get(
                    f"{self.base_url}/player/{roster_entry.player_id}/landing"
                )
                
                if response.status_code != 200:
                    continue
                
                data = response.json()
                
                # Find season stats
                season_stats = None
                for season_stat in data.get("seasonTotals", []):
                    if season_stat.get("season") == int(season_id.replace('-', '')):
                        season_stats = season_stat
                        break
                
                if not season_stats:
                    continue
                
                # Check if stats already exist
                existing = self.db.query(PlayerSeasonStats).filter(
                    PlayerSeasonStats.player_id == roster_entry.player_id,
                    PlayerSeasonStats.season_id == season_id,
                    PlayerSeasonStats.team_id == roster_entry.team_id
                ).first()
                
                if existing:
                    continue
                
                # Create player stats
                player_stats = PlayerSeasonStats(
                    player_id=roster_entry.player_id,
                    season_id=season_id,
                    team_id=roster_entry.team_id,
                    games_played=season_stats.get("gamesPlayed", 0),
                    goals=season_stats.get("goals", 0),
                    assists=season_stats.get("assists", 0),
                    points=season_stats.get("points", 0),
                    shots=season_stats.get("shots", 0),
                    shot_percentage=season_stats.get("shootingPct"),
                    power_play_goals=season_stats.get("powerPlayGoals", 0),
                    power_play_assists=season_stats.get("powerPlayAssists", 0),
                    power_play_points=season_stats.get("powerPlayPoints", 0),
                    short_handed_goals=season_stats.get("shorthandedGoals", 0),
                    short_handed_assists=season_stats.get("shorthandedAssists", 0),
                    short_handed_points=season_stats.get("shorthandedPoints", 0),
                    hits=season_stats.get("hits", 0),
                    blocks=season_stats.get("blockedShots", 0),
                    penalty_minutes=season_stats.get("pim", 0),
                    plus_minus=season_stats.get("plusMinus", 0),
                    avg_toi=season_stats.get("avgToi"),
                    faceoff_wins=season_stats.get("faceoffWins", 0),
                    faceoff_losses=season_stats.get("faceoffLosses", 0),
                    faceoff_percentage=season_stats.get("faceoffWinPct")
                )
                
                self.db.add(player_stats)
                stats_added += 1
                
                # Commit every 50 records to avoid huge transactions
                if stats_added % 50 == 0:
                    self.db.commit()
                    logger.info(f"Processed {stats_added} player stat records...")
                
            except Exception as e:
                logger.warning(f"Error collecting stats for player {roster_entry.player_id}: {e}")
                continue
        
        logger.info(f"Added {stats_added} player stat records")
        return stats_added