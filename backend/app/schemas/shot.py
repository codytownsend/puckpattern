from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime


class ShotBase(BaseModel):
    shot_type: str
    x_coordinate: float
    y_coordinate: float
    period: int
    time_elapsed: float
    distance: Optional[float] = None
    angle: Optional[float] = None
    goal: bool = False
    is_scoring_chance: Optional[bool] = False
    is_high_danger: Optional[bool] = False
    rush_shot: Optional[bool] = False
    rebound_shot: Optional[bool] = False
    frozen_shot: Optional[bool] = False


class ShotCreate(ShotBase):
    game_id: str
    shooter_id: str
    team_id: str
    goalie_id: Optional[str] = None
    primary_assist_id: Optional[str] = None
    secondary_assist_id: Optional[str] = None
    preceding_event_id: Optional[int] = None


class Shot(ShotBase):
    id: int
    event_id: int
    shooter_id: int
    team_id: int
    game_id: str
    goalie_id: Optional[int] = None
    primary_assist_id: Optional[int] = None
    secondary_assist_id: Optional[int] = None
    preceding_event_id: Optional[int] = None
    xg: Optional[float] = None
    created_at: datetime
    
    class Config:
        orm_mode = True


class ShotResponse(BaseModel):
    id: int
    shot_type: str
    x_coordinate: float
    y_coordinate: float
    period: int
    time_elapsed: float
    distance: Optional[float] = None
    angle: Optional[float] = None
    goal: bool
    xg: Optional[float] = None
    shooter: Dict[str, Any]
    team: Dict[str, Any]
    game: Dict[str, Any]
    goalie: Optional[Dict[str, Any]] = None
    primary_assist: Optional[Dict[str, Any]] = None
    secondary_assist: Optional[Dict[str, Any]] = None
    is_scoring_chance: Optional[bool] = None
    is_high_danger: Optional[bool] = None
    rush_shot: Optional[bool] = None
    rebound_shot: Optional[bool] = None
    frozen_shot: Optional[bool] = None
    
    class Config:
        orm_mode = True


class HeatmapPoint(BaseModel):
    x: float
    y: float
    value: float
    type: Optional[str] = None  # For distinguishing shot types


class ShotHeatmapResponse(BaseModel):
    points: List[HeatmapPoint]
    max_value: float
    total_shots: int
    total_goals: int
    average_xg: float
    metadata: Dict[str, Any]
    
    class Config:
        orm_mode = True


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
    
    class Config:
        orm_mode = True