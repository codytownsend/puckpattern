from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ShotMetrics(BaseModel):
    """Schema for shot-based metrics."""
    total_shots: int
    goals: int
    shooting_percentage: float
    total_xg: float
    avg_xg: float
    xg_performance: float


class PlayerMetrics(BaseModel):
    """Schema for player performance metrics."""
    player_id: str
    name: str
    position: str
    team: Optional[Dict[str, Any]] = None
    ecr: float = Field(..., description="Entry Conversion Rate")
    pri: float = Field(..., description="Puck Recovery Impact")
    shot_metrics: ShotMetrics
    total_events: int
    ice_plus: float = Field(..., description="ICE+ Composite Score")


class TeamMetrics(BaseModel):
    """Schema for team performance metrics."""
    team_id: str
    name: str
    abbreviation: str
    ecr: float = Field(..., description="Entry Conversion Rate")
    pri: float = Field(..., description="Puck Recovery Impact")
    shot_metrics: ShotMetrics
    total_events: int
    player_count: int


class MetricValue(BaseModel):
    """Schema for individual metric value."""
    name: str
    value: float
    description: str