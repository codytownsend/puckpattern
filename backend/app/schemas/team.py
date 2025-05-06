from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime


class TeamBase(BaseModel):
    """Base team schema with common attributes."""
    name: str
    abbreviation: str


class TeamCreate(TeamBase):
    """Schema for creating a new team."""
    team_id: str  # External identifier (e.g., NHL API ID)


class TeamUpdate(BaseModel):
    """Schema for updating a team (all fields optional)."""
    name: Optional[str] = None
    abbreviation: Optional[str] = None


class Team(TeamBase):
    """Complete team schema for responses."""
    id: int
    team_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


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
    
    # Advanced stats can be added here
    xg_for: Optional[float] = None
    xg_against: Optional[float] = None
    system_metrics: Optional[Dict[str, Any]] = None

    class Config:
        orm_mode = True


class TeamList(BaseModel):
    """Schema for returning a list of teams with pagination."""
    teams: List[Team]
    total: int
    skip: int
    limit: int