from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime


class EventBase(BaseModel):
    """Base game event schema with common attributes."""
    event_type: str
    period: int
    time_elapsed: float
    time_remaining: Optional[str] = None
    x_coordinate: Optional[float] = None
    y_coordinate: Optional[float] = None
    situation_code: Optional[str] = None
    strength_code: Optional[str] = None  # E.g. "EV", "PP", "SH"
    is_scoring_play: Optional[bool] = None
    is_penalty: Optional[bool] = None
    sort_order: Optional[int] = None
    event_id: Optional[int] = None  # NHL event ID


class EventCreate(EventBase):
    """Schema for creating a new game event."""
    game_id: int
    player_id: Optional[int] = None  # External player_id
    team_id: Optional[int] = None    # External team_id


class EventUpdate(BaseModel):
    """Schema for updating a game event (all fields optional)."""
    event_type: Optional[str] = None
    period: Optional[int] = None
    time_elapsed: Optional[float] = None
    time_remaining: Optional[str] = None
    x_coordinate: Optional[float] = None
    y_coordinate: Optional[float] = None
    player_id: Optional[int] = None  # External player_id
    team_id: Optional[int] = None    # External team_id
    strength_code: Optional[str] = None
    situation_code: Optional[str] = None
    is_scoring_play: Optional[bool] = None
    is_penalty: Optional[bool] = None
    sort_order: Optional[int] = None
    event_id: Optional[int] = None


class Event(EventBase):
    """Complete game event schema for responses."""
    id: int
    game_id: str
    player_id: Optional[int] = None
    team_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EventWithRelations(Event):
    """Game event schema with related entities."""
    player: Optional[Dict[str, Any]] = None
    team: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class PlayByPlayEvent(BaseModel):
    """Schema for play-by-play event details."""
    id: int
    event_type: str
    period: int
    time_elapsed: float
    time_remaining: Optional[str] = None
    coordinates: Dict[str, Optional[float]]
    team: Optional[Dict[str, Any]] = None
    player: Optional[Dict[str, Any]] = None
    situation_code: Optional[str] = None
    strength: Optional[Dict[str, Any]] = None
    is_scoring_play: Optional[bool] = None
    is_penalty: Optional[bool] = None
    details: Optional[Dict[str, Any]] = None
    participants: Optional[List[Dict[str, Any]]] = None
    
    model_config = ConfigDict(from_attributes=True)


class EventList(BaseModel):
    """Schema for returning a list of events with pagination."""
    events: List[EventWithRelations]
    total: int
    skip: int
    limit: int