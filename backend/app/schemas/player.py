from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime, date


class PlayerBase(BaseModel):
    """Base player schema with common attributes."""
    name: str
    position: str
    sweater_number: Optional[str] = None
    player_slug: Optional[str] = None
    height_in_inches: Optional[int] = None
    height_in_cm: Optional[float] = None
    weight_in_pounds: Optional[int] = None
    weight_in_kg: Optional[float] = None
    birth_date: Optional[date] = None
    birth_city: Optional[str] = None
    birth_state_province: Optional[str] = None
    birth_country: Optional[str] = None
    shoots_catches: Optional[str] = None
    headshot_url: Optional[str] = None


class PlayerCreate(PlayerBase):
    """Schema for creating a new player."""
    player_id: int  # External identifier (e.g., NHL API ID)
    team_id: Optional[int] = None  # External team_id


class PlayerUpdate(BaseModel):
    """Schema for updating a player (all fields optional)."""
    name: Optional[str] = None
    position: Optional[str] = None
    team_id: Optional[int] = None  # External team_id
    sweater_number: Optional[str] = None
    player_slug: Optional[str] = None
    height_in_inches: Optional[int] = None
    height_in_cm: Optional[float] = None
    weight_in_pounds: Optional[int] = None
    weight_in_kg: Optional[float] = None
    birth_date: Optional[date] = None
    birth_city: Optional[str] = None
    birth_state_province: Optional[str] = None
    birth_country: Optional[str] = None
    shoots_catches: Optional[str] = None
    headshot_url: Optional[str] = None


class Player(PlayerBase):
    """Complete player schema for responses."""
    id: int
    player_id: str
    team_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PlayerWithTeam(Player):
    """Player schema with team information."""
    team: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


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
    
    # Additional stats from NHL API
    face_off_pct: Optional[float] = None
    power_play_goals: Optional[int] = None
    power_play_points: Optional[int] = None
    short_handed_goals: Optional[int] = None
    short_handed_points: Optional[int] = None
    game_winning_goals: Optional[int] = None
    overtime_goals: Optional[int] = None
    
    # Custom metrics
    ecr: Optional[float] = None  # Entry Conversion Rate
    pri: Optional[float] = None  # Puck Recovery Impact
    pdi: Optional[float] = None  # Positional Disruption Index
    xg_delta_psm: Optional[float] = None  # xGΔPSM
    sfs: Optional[float] = None  # System Fidelity Score
    omc: Optional[float] = None  # Offensive Momentum Curve

    model_config = ConfigDict(from_attributes=True)


class PlayerList(BaseModel):
    """Schema for returning a list of players with pagination."""
    players: List[PlayerWithTeam]
    total: int
    skip: int
    limit: int