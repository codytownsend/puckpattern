from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime


class GameBase(BaseModel):
    """Base game schema with common attributes."""
    date: datetime
    season: str
    status: str = "scheduled"
    period: Optional[int] = 1
    time_remaining: Optional[str] = "20:00"
    home_score: Optional[int] = 0
    away_score: Optional[int] = 0
    venue_name: Optional[str] = None
    venue_city: Optional[str] = None
    game_type: Optional[int] = 2  # 2 for regular season, 3 for playoffs
    neutral_site: Optional[bool] = False


class GameCreate(GameBase):
    """Schema for creating a new game."""
    game_id: str  # External identifier (e.g., NHL API ID)
    home_team_id: str  # External team_id
    away_team_id: str  # External team_id


class GameUpdate(BaseModel):
    """Schema for updating a game (all fields optional)."""
    date: Optional[datetime] = None
    season: Optional[str] = None
    status: Optional[str] = None
    period: Optional[int] = None
    time_remaining: Optional[str] = None
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    home_team_id: Optional[str] = None  # External team_id
    away_team_id: Optional[str] = None  # External team_id
    venue_name: Optional[str] = None
    venue_city: Optional[str] = None
    game_type: Optional[int] = None
    neutral_site: Optional[bool] = None


class Game(GameBase):
    """Complete game schema for responses."""
    id: int
    game_id: str
    home_team_id: int
    away_team_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class GameWithTeams(Game):
    """Game schema with team information."""
    home_team: Dict[str, Any]
    away_team: Dict[str, Any]

    class Config:
        orm_mode = True


class GameWithStats(GameWithTeams):
    """Game schema with additional statistics."""
    home_team_stats: Optional[Dict[str, Any]] = None
    away_team_stats: Optional[Dict[str, Any]] = None
    home_team_sog: Optional[int] = None
    away_team_sog: Optional[int] = None
    home_team_faceoff_pct: Optional[float] = None
    away_team_faceoff_pct: Optional[float] = None
    home_team_hits: Optional[int] = None
    away_team_hits: Optional[int] = None
    home_team_blocks: Optional[int] = None
    away_team_blocks: Optional[int] = None
    home_team_power_play: Optional[Dict[str, Any]] = None
    away_team_power_play: Optional[Dict[str, Any]] = None
    
    class Config:
        orm_mode = True


class GameList(BaseModel):
    """Schema for returning a list of games with pagination."""
    games: List[GameWithTeams]
    total: int
    skip: int
    limit: int
    
    
class PeriodSummary(BaseModel):
    """Schema for period summary information."""
    period: int
    home_goals: int = 0
    away_goals: int = 0
    home_shots: int = 0
    away_shots: int = 0
    goals: List[Dict[str, Any]] = []