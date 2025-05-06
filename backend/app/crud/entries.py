from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_, desc, asc

from app.models.base import Team, Player
from app.models.analytics import ZoneEntry
from app.schemas.entry import EntryCreate, EntryUpdate


def get_entries(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    game_id: Optional[str] = None,
    team_id: Optional[str] = None,
    player_id: Optional[str] = None,
    entry_type: Optional[str] = None,
    controlled: Optional[bool] = None,
    lead_to_shot: Optional[bool] = None
) -> List[ZoneEntry]:
    """
    Get zone entries with various filters.
    """
    query = db.query(ZoneEntry).options(
        joinedload(ZoneEntry.event),
        joinedload(ZoneEntry.player),
        joinedload(ZoneEntry.defender)
    )
    
    if game_id:
        query = query.join(ZoneEntry.event).filter(ZoneEntry.event.has(game_id=game_id))
    
    if team_id:
        # Get the internal team ID first
        team = db.query(Team).filter(Team.team_id == team_id).first()
        if team:
            query = query.join(ZoneEntry.event).filter(ZoneEntry.event.has(team_id=team.id))
    
    if player_id:
        # Get the internal player ID first
        player = db.query(Player).filter(Player.player_id == player_id).first()
        if player:
            query = query.filter(ZoneEntry.player_id == player.id)
    
    if entry_type:
        query = query.filter(ZoneEntry.entry_type == entry_type)
    
    if controlled is not None:
        query = query.filter(ZoneEntry.controlled == controlled)
    
    if lead_to_shot is not None:
        query = query.filter(ZoneEntry.lead_to_shot == lead_to_shot)
    
    return query.offset(skip).limit(limit).all()


def get_entry_by_id(db: Session, entry_id: int) -> Optional[ZoneEntry]:
    """
    Get a specific zone entry by ID.
    """
    return db.query(ZoneEntry).options(
        joinedload(ZoneEntry.event),
        joinedload(ZoneEntry.player),
        joinedload(ZoneEntry.defender)
    ).filter(ZoneEntry.id == entry_id).first()


def create_entry(db: Session, entry: EntryCreate) -> ZoneEntry:
    """
    Create a new zone entry.
    """
    # Get player and defender IDs if provided
    player_id = None
    if entry.player_id:
        player = db.query(Player).filter(Player.player_id == entry.player_id).first()
        if player:
            player_id = player.id
    
    defender_id = None
    if entry.defender_id:
        defender = db.query(Player).filter(Player.player_id == entry.defender_id).first()
        if defender:
            defender_id = defender.id
    
    # Create zone entry
    db_entry = ZoneEntry(
        event_id=entry.event_id,
        entry_type=entry.entry_type,
        controlled=entry.controlled,
        player_id=player_id,
        defender_id=defender_id,
        lead_to_shot=entry.lead_to_shot,
        lead_to_shot_time=entry.lead_to_shot_time
    )
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    return db_entry


def update_entry(db: Session, entry_id: int, entry_update: EntryUpdate) -> Optional[ZoneEntry]:
    """
    Update a zone entry.
    """
    db_entry = get_entry_by_id(db, entry_id)
    if not db_entry:
        return None
    
    entry_data = entry_update.dict(exclude_unset=True)
    
    # Handle player_id and defender_id if provided
    if "player_id" in entry_data:
        player_id = entry_data.pop("player_id")
        if player_id:
            player = db.query(Player).filter(Player.player_id == player_id).first()
            if player:
                entry_data["player_id"] = player.id
            else:
                entry_data["player_id"] = None
        else:
            entry_data["player_id"] = None
    
    if "defender_id" in entry_data:
        defender_id = entry_data.pop("defender_id")
        if defender_id:
            defender = db.query(Player).filter(Player.player_id == defender_id).first()
            if defender:
                entry_data["defender_id"] = defender.id
            else:
                entry_data["defender_id"] = None
        else:
            entry_data["defender_id"] = None
    
    for key, value in entry_data.items():
        setattr(db_entry, key, value)
    
    db.commit()
    db.refresh(db_entry)
    return db_entry


def delete_entry(db: Session, entry_id: int) -> bool:
    """
    Delete a zone entry.
    """
    db_entry = get_entry_by_id(db, entry_id)
    if not db_entry:
        return False
    
    db.delete(db_entry)
    db.commit()
    return True


def get_player_entries_stats(db: Session, player_id: str) -> Dict[str, Any]:
    """
    Get zone entry statistics for a player.
    """
    # Get player
    player = db.query(Player).filter(Player.player_id == player_id).first()
    if not player:
        return {"error": "Player not found"}
    
    # Get all entries by this player
    entries = db.query(ZoneEntry).filter(ZoneEntry.player_id == player.id).all()
    
    # Calculate stats
    total_entries = len(entries)
    controlled_entries = sum(1 for entry in entries if entry.controlled)
    successful_entries = sum(1 for entry in entries if entry.lead_to_shot)
    
    # Entry types
    entry_types = {}
    for entry in entries:
        entry_type = entry.entry_type
        if entry_type not in entry_types:
            entry_types[entry_type] = 0
        entry_types[entry_type] += 1
    
    # Calculate ratios
    controlled_entry_ratio = controlled_entries / total_entries if total_entries > 0 else 0
    entry_success_ratio = successful_entries / total_entries if total_entries > 0 else 0
    
    return {
        "player_id": player_id,
        "name": player.name,
        "total_entries": total_entries,
        "controlled_entries": controlled_entries,
        "successful_entries": successful_entries,
        "controlled_entry_ratio": controlled_entry_ratio,
        "entry_success_ratio": entry_success_ratio,
        "entry_types": entry_types
    }


def get_team_entries_stats(db: Session, team_id: str) -> Dict[str, Any]:
    """
    Get zone entry statistics for a team.
    """
    # Get team
    team = db.query(Team).filter(Team.team_id == team_id).first()
    if not team:
        return {"error": "Team not found"}
    
    # Get all entries by this team
    entries = db.query(ZoneEntry).join(ZoneEntry.event).filter(ZoneEntry.event.has(team_id=team.id)).all()
    
    # Calculate stats
    total_entries = len(entries)
    controlled_entries = sum(1 for entry in entries if entry.controlled)
    successful_entries = sum(1 for entry in entries if entry.lead_to_shot)
    
    # Entry types
    entry_types = {}
    for entry in entries:
        entry_type = entry.entry_type
        if entry_type not in entry_types:
            entry_types[entry_type] = 0
        entry_types[entry_type] += 1
    
    # Calculate ratios
    controlled_entry_ratio = controlled_entries / total_entries if total_entries > 0 else 0
    entry_success_ratio = successful_entries / total_entries if total_entries > 0 else 0
    
    # Get top players
    player_entries = {}
    for entry in entries:
        if entry.player_id is None:
            continue
        
        if entry.player_id not in player_entries:
            player_entries[entry.player_id] = 0
        player_entries[entry.player_id] += 1
    
    top_players = []
    for player_id, count in sorted(player_entries.items(), key=lambda x: x[1], reverse=True)[:5]:
        player = db.query(Player).filter(Player.id == player_id).first()
        if player:
            top_players.append({
                "id": player.id,
                "player_id": player.player_id,
                "name": player.name,
                "entries": count
            })
    
    return {
        "team_id": team_id,
        "name": team.name,
        "total_entries": total_entries,
        "controlled_entries": controlled_entries,
        "successful_entries": successful_entries,
        "controlled_entry_ratio": controlled_entry_ratio,
        "entry_success_ratio": entry_success_ratio,
        "entry_types": entry_types,
        "top_players": top_players
    }