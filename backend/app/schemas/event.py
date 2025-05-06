from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class EventBase(BaseModel):
    """Base game event schema with common attributes."""
    event_type: str
    period: int
    time_elapsed: float
    x_coordinate: Optional[float] = None
    y_coordinate: Optional[float] = None


class EventCreate(EventBase):
    """Schema for creating a new game event."""
    game_id: str
    player_id: Optional[str] = None  # External player_id
    team_id: Optional[str] = None    # External team_id


class EventUpdate(BaseModel):
    """Schema for updating a game event (all fields optional)."""
    event_type: Optional[str] = None
    period: Optional[int] = None
    time_elapsed: Optional[float] = None
    x_coordinate: Optional[float] = None
    y_coordinate: Optional[float] = None
    player_id: Optional[str] = None  # External player_id
    team_id: Optional[str] = None    # External team_id


class Event(EventBase):
    """Complete game event schema for responses."""
    id: int
    game_id: str
    player_id: Optional[int] = None
    team_id: Optional[int] = None
    created_at: datetime

    class Config:
        orm_mode = True


class EventWithRelations(Event):
    """Game event schema with related entities."""
    player: Optional[Dict[str, Any]] = None
    team: Optional[Dict[str, Any]] = None

    class Config:
        orm_mode = True


class PlayByPlayEvent(BaseModel):
    """Schema for play-by-play event details."""
    id: int
    event_type: str
    period: int
    time_elapsed: float
    coordinates: Dict[str, Optional[float]]
    team: Optional[Dict[str, Any]] = None
    player: Optional[Dict[str, Any]] = None
    
    class Config:
        orm_mode = True


class EventList(BaseModel):
    """Schema for returning a list of events with pagination."""
    events: List[EventWithRelations]
    total: int
    skip: int
    limit: int