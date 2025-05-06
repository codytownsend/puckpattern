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
    high_danger_shots: Optional[int] = None
    scoring_chances: Optional[int] = None
    rush_shots: Optional[int] = None
    rebound_shots: Optional[int] = None


class ZoneEntryMetrics(BaseModel):
    """Schema for zone entry metrics."""
    total_entries: int
    controlled_entries: int
    dump_ins: int
    success_rate: float
    entry_to_chance_pct: float
    entry_to_shot_pct: float


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
    
    # Additional metrics from NHL API
    face_off_pct: Optional[float] = None
    power_play_goals: Optional[int] = None
    power_play_points: Optional[int] = None
    short_handed_goals: Optional[int] = None
    short_handed_points: Optional[int] = None
    game_winning_goals: Optional[int] = None
    overtime_goals: Optional[int] = None
    zone_entries: Optional[ZoneEntryMetrics] = None
    
    # Custom metrics
    pdi: Optional[float] = Field(None, description="Positional Disruption Index")
    xg_delta_psm: Optional[float] = Field(None, description="xGΔPSM")
    sfs: Optional[float] = Field(None, description="System Fidelity Score")
    omc: Optional[float] = Field(None, description="Offensive Momentum Curve")


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
    
    # Additional metrics from NHL API
    faceoff_win_pct: Optional[float] = None
    power_play_pct: Optional[float] = None
    penalty_kill_pct: Optional[float] = None
    hits_per_game: Optional[float] = None
    blocks_per_game: Optional[float] = None
    zone_entries: Optional[ZoneEntryMetrics] = None
    
    # Custom metrics
    team_pdi: Optional[float] = Field(None, description="Team Positional Disruption Index")
    system_metrics: Optional[Dict[str, Any]] = None
    forecheck_style: Optional[str] = None
    defensive_structure: Optional[str] = None
    pp_formation: Optional[str] = None
    pk_formation: Optional[str] = None


class MetricValue(BaseModel):
    """Schema for individual metric value."""
    name: str
    value: float
    description: str