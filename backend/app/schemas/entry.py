from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime


class EntryBase(BaseModel):
    """Base zone entry schema with common attributes."""
    entry_type: str
    controlled: bool = False
    lead_to_shot: bool = False
    lead_to_shot_time: Optional[float] = None
    attack_speed: Optional[str] = None  # "RUSH", "CONTROLLED", etc.
    sequence_number: Optional[int] = None


class EntryCreate(EntryBase):
    """Schema for creating a new zone entry."""
    event_id: int
    player_id: Optional[str] = None  # External player_id
    defender_id: Optional[str] = None  # External player_id


class EntryUpdate(BaseModel):
    """Schema for updating a zone entry (all fields optional)."""
    entry_type: Optional[str] = None
    controlled: Optional[bool] = None
    player_id: Optional[str] = None  # External player_id
    defender_id: Optional[str] = None  # External player_id
    lead_to_shot: Optional[bool] = None
    lead_to_shot_time: Optional[float] = None
    attack_speed: Optional[str] = None
    sequence_number: Optional[int] = None


class Entry(EntryBase):
    """Complete zone entry schema for responses."""
    id: int
    event_id: int
    player_id: Optional[int] = None
    defender_id: Optional[int] = None
    created_at: datetime

    class Config:
        orm_mode = True


class EntryWithRelations(Entry):
    """Zone entry schema with related entities."""
    event: Optional[Dict[str, Any]] = None
    player: Optional[Dict[str, Any]] = None
    defender: Optional[Dict[str, Any]] = None

    class Config:
        orm_mode = True


class EntryList(BaseModel):
    """Schema for returning a list of zone entries with pagination."""
    entries: List[EntryWithRelations]
    total: int
    skip: int
    limit: int


class PlayerEntryStats(BaseModel):
    """Schema for player zone entry statistics."""
    player_id: str
    name: str
    total_entries: int
    controlled_entries: int
    successful_entries: int
    controlled_entry_ratio: float
    entry_success_ratio: float
    entry_types: Dict[str, int]
    rush_entries: Optional[int] = None
    entries_with_possession: Optional[int] = None


class TeamEntryStats(BaseModel):
    """Schema for team zone entry statistics."""
    team_id: str
    name: str
    total_entries: int
    controlled_entries: int
    successful_entries: int
    controlled_entry_ratio: float
    entry_success_ratio: float
    entry_types: Dict[str, int]
    top_players: List[Dict[str, Any]]
    rush_entries: Optional[int] = None
    entries_with_possession: Optional[int] = None