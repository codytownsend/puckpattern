from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime


class PlayerBase(BaseModel):
    """Base player schema with common attributes."""
    name: str
    position: str


class PlayerCreate(PlayerBase):
    """Schema for creating a new player."""
    player_id: str  # External identifier (e.g., NHL API ID)
    team_id: Optional[str] = None  # External team_id


class PlayerUpdate(BaseModel):
    """Schema for updating a player (all fields optional)."""
    name: Optional[str] = None
    position: Optional[str] = None
    team_id: Optional[str] = None  # External team_id


class Player(PlayerBase):
    """Complete player schema for responses."""
    id: int
    player_id: str
    team_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class PlayerWithTeam(Player):
    """Player schema with team information."""
    team: Optional[Dict[str, Any]] = None

    class Config:
        orm_mode = True


class PlayerWithStats(PlayerWithTeam):
    """Player schema with additional statistics."""
    games_played: int = 0
    goals: int = 0
    assists: int = 0
    points: int = 0
    shots: int = 0
    shot_percentage: float = 0.0
    
    # Advanced stats
    xg: Optional[float] = None
    xg_per_game: Optional[float] = None
    ice_plus: Optional[float] = None
    
    # Custom metrics
    ecr: Optional[float] = None  # Entry Conversion Rate
    pri: Optional[float] = None  # Puck Recovery Impact
    pdi: Optional[float] = None  # Positional Disruption Index
    xg_delta_psm: Optional[float] = None  # xGΔPSM
    sfs: Optional[float] = None  # System Fidelity Score
    omc: Optional[float] = None  # Offensive Momentum Curve

    class Config:
        orm_mode = True


class PlayerList(BaseModel):
    """Schema for returning a list of players with pagination."""
    players: List[PlayerWithTeam]
    total: int
    skip: int
    limit: int