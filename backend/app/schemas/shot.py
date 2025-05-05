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
    
    class Config:
        orm_mode = True


class HeatmapPoint(BaseModel):
    x: float
    y: float
    value: float


class ShotHeatmapResponse(BaseModel):
    points: List[HeatmapPoint]
    max_value: float
    total_shots: int
    total_goals: int
    average_xg: float
    metadata: Dict[str, Any]
    
    class Config:
        orm_mode = True