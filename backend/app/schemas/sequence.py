from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class EventReference(BaseModel):
    """Schema for referencing an event in a sequence."""
    id: int
    event_type: str
    period: int
    time_elapsed: float
    coordinates: Dict[str, Optional[float]]
    player: Optional[Dict[str, Any]] = None
    team: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class CycleSequence(BaseModel):
    """Schema for a cycle sequence."""
    id: int
    events: List[EventReference]
    duration: float
    zone: str
    team_id: int
    team_name: str
    player_ids: List[int]
    pass_count: int
    shot_resulted: bool = False

    model_config = ConfigDict(from_attributes=True)


class RushPlay(BaseModel):
    """Schema for a rush play sequence."""
    id: int
    events: List[EventReference]
    duration: float
    start_zone: str
    end_zone: str
    team_id: int
    team_name: str
    primary_player_id: Optional[int] = None
    distance_covered: Optional[float] = None
    shot_resulted: bool = False
    goal_resulted: bool = False

    model_config = ConfigDict(from_attributes=True)


class SequenceList(BaseModel):
    """Schema for a list of sequences."""
    sequences: List[Dict[str, Any]]
    total: int
    sequence_type: str
    game_id: Optional[str] = None
    team_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)