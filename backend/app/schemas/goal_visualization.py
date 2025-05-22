from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class FramePlayer(BaseModel):
    """Schema for player position in a visualization frame."""
    id: str
    player_id: Optional[str] = None
    x: float
    y: float
    sweater_number: Optional[str] = None
    team_id: Optional[str] = None
    team_abbrev: Optional[str] = None

class Frame(BaseModel):
    """Schema for a single frame in goal visualization."""
    time_stamp: int
    on_ice: Dict[str, FramePlayer]

class GoalVisualization(BaseModel):
    """Schema for complete goal visualization data."""
    goal_id: str
    frames: List[Frame]
    meta: Dict[str, Any]  # Additional metadata about the goal