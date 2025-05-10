from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class PlayerAnalytics(BaseModel):
    """Schema for player analytics."""
    player_id: int
    name: str
    team: Optional[Dict[str, Any]] = None
    position: str
    ecr: float = Field(..., description="Entry Conversion Rate")
    pri: float = Field(..., description="Puck Recovery Impact")
    pdi: float = Field(..., description="Positional Disruption Index")
    xg_delta_psm: float = Field(..., description="Expected Goals Delta from Pass Shot Movement")
    shot_metrics: Dict[str, Any]
    entries: Dict[str, Any]
    ice_plus: float = Field(..., description="ICE+ Composite Score")


class TeamAnalytics(BaseModel):
    """Schema for team analytics."""
    team_id: int
    name: str
    abbreviation: str
    ecr: float = Field(..., description="Entry Conversion Rate")
    pri: float = Field(..., description="Puck Recovery Impact")
    pdi: float = Field(..., description="Positional Disruption Index")
    shot_metrics: Dict[str, Any]