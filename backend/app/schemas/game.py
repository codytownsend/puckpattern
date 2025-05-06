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
    
    class Config:
        orm_mode = True


class GameList(BaseModel):
    """Schema for returning a list of games with pagination."""
    games: List[GameWithTeams]
    total: int
    skip: int
    limit: int