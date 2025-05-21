from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime


class TeamBase(BaseModel):
    """Base team schema with common attributes."""
    name: str
    abbreviation: str
    city_name: Optional[str] = None
    team_name: Optional[str] = None
    division: Optional[str] = None
    conference: Optional[str] = None
    venue_name: Optional[str] = None
    venue_city: Optional[str] = None
    official_site_url: Optional[str] = None
    active: bool = True


class TeamCreate(TeamBase):
    """Schema for creating a new team."""
    team_id: int  # External identifier (e.g., NHL API ID)


class TeamUpdate(BaseModel):
    """Schema for updating a team (all fields optional)."""
    name: Optional[str] = None
    abbreviation: Optional[str] = None
    city_name: Optional[str] = None
    team_name: Optional[str] = None
    division: Optional[str] = None
    conference: Optional[str] = None
    venue_name: Optional[str] = None
    venue_city: Optional[str] = None
    official_site_url: Optional[str] = None
    active: Optional[bool] = None


class Team(TeamBase):
    """Complete team schema for responses."""
    id: int
    team_id: str
    franchise_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class TeamWithStats(Team):
    """Team schema with additional statistics."""
    player_count: int = 0
    games_played: int = 0
    wins: int = 0
    losses: int = 0
    overtime_losses: int = 0
    points: int = 0
    goals_for: int = 0
    goals_against: int = 0
    created_at: Optional[datetime] = None
    
    # Advanced stats
    xg_for: Optional[float] = None
    xg_against: Optional[float] = None
    system_metrics: Optional[Dict[str, Any]] = None
    faceoff_win_pct: Optional[float] = None
    power_play_pct: Optional[float] = None
    penalty_kill_pct: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class TeamList(BaseModel):
    """Schema for returning a list of teams with pagination."""
    teams: List[Team]
    total: int
    skip: int
    limit: int