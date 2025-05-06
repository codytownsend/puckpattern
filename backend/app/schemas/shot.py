from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime


class ShotBase(BaseModel):
    """Base schema for shot data with common attributes."""
    shot_type: str
    distance: Optional[float] = None
    angle: Optional[float] = None
    goal: bool = False
    xg: Optional[float] = None
    is_scoring_chance: Optional[bool] = False
    is_high_danger: Optional[bool] = False
    rush_shot: Optional[bool] = False
    rebound_shot: Optional[bool] = False
    frozen_shot: Optional[bool] = False


class ShotCreate(ShotBase):
    """Schema for creating a new shot event."""
    game_id: int
    period: int
    time_elapsed: float
    x_coordinate: float
    y_coordinate: float
    shooter_id: int  # External player_id
    team_id: int     # External team_id
    goalie_id: Optional[int] = None  # External player_id
    primary_assist_id: Optional[int] = None  # External player_id
    secondary_assist_id: Optional[int] = None  # External player_id
    preceding_event_id: Optional[int] = None
    situation_code: Optional[str] = None  # "EV", "PP", "SH"


class ShotUpdate(BaseModel):
    """Schema for updating a shot (all fields optional)."""
    shot_type: Optional[str] = None
    distance: Optional[float] = None
    angle: Optional[float] = None
    goal: Optional[bool] = None
    xg: Optional[float] = None
    shooter_id: Optional[int] = None  # External player_id
    goalie_id: Optional[int] = None  # External player_id
    primary_assist_id: Optional[int] = None  # External player_id
    secondary_assist_id: Optional[int] = None  # External player_id
    preceding_event_id: Optional[int] = None
    is_scoring_chance: Optional[bool] = None
    is_high_danger: Optional[bool] = None
    rush_shot: Optional[bool] = None
    rebound_shot: Optional[bool] = None
    frozen_shot: Optional[bool] = None


class Shot(ShotBase):
    """Complete shot schema for responses."""
    id: int
    event_id: int
    shooter_id: int
    created_at: datetime
    goalie_id: Optional[int] = None
    primary_assist_id: Optional[int] = None
    secondary_assist_id: Optional[int] = None
    preceding_event_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class ShotResponse(BaseModel):
    """Schema for shot response with related entities."""
    id: int
    shot_type: str
    distance: Optional[float] = None
    angle: Optional[float] = None
    goal: bool
    xg: Optional[float] = None
    shooter: Dict[str, Any]
    team: Dict[str, Any]
    game: Dict[str, Any]
    period: int
    time_elapsed: float
    x_coordinate: float
    y_coordinate: float
    goalie: Optional[Dict[str, Any]] = None
    primary_assist: Optional[Dict[str, Any]] = None
    secondary_assist: Optional[Dict[str, Any]] = None
    is_scoring_chance: Optional[bool] = None
    is_high_danger: Optional[bool] = None
    rush_shot: Optional[bool] = None
    rebound_shot: Optional[bool] = None
    frozen_shot: Optional[bool] = None
    situation_code: Optional[str] = None  # "EV", "PP", "SH"
    
    model_config = ConfigDict(from_attributes=True)


class HeatmapPoint(BaseModel):
    """Schema for a heatmap data point."""
    x: float
    y: float
    value: float
    type: Optional[str] = None  # For distinguishing shot types


class ShotHeatmapResponse(BaseModel):
    """Schema for shot heatmap visualization response."""
    points: List[HeatmapPoint]
    max_value: float
    total_shots: int
    total_goals: int
    average_xg: float
    metadata: Dict[str, Any]
    
    model_config = ConfigDict(from_attributes=True)


class ShotBreakdown(BaseModel):
    """Schema for shot breakdown statistics."""
    total: int
    goals: int
    shooting_pct: float
    xg: float
    xg_per_shot: float
    high_danger: int = 0
    medium_danger: int = 0
    low_danger: int = 0
    rush_shots: int = 0
    rebound_shots: int = 0
    shot_types: Dict[str, int] = {}
    shot_zones: Dict[str, int] = {}
    
    model_config = ConfigDict(from_attributes=True)