from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.entry import Entry, EntryCreate, EntryUpdate, EntryWithRelations, EntryList, PlayerEntryStats, TeamEntryStats
from app.crud import entries as crud_entries

router = APIRouter()


@router.get("/", response_model=EntryList)
def get_entries(
    skip: int = 0,
    limit: int = 100,
    game_id: Optional[str] = None,
    team_id: Optional[str] = None,
    player_id: Optional[str] = None,
    entry_type: Optional[str] = None,
    controlled: Optional[bool] = None,
    lead_to_shot: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """
    Get all zone entries with optional filtering and pagination.
    """
    db_entries = crud_entries.get_entries(
        db, 
        skip=skip, 
        limit=limit, 
        game_id=game_id,
        team_id=team_id,
        player_id=player_id,
        entry_type=entry_type,
        controlled=controlled,
        lead_to_shot=lead_to_shot
    )
    
    # Get total count for pagination
    total_entries = len(crud_entries.get_entries(
        db, 
        game_id=game_id,
        team_id=team_id,
        player_id=player_id,
        entry_type=entry_type,
        controlled=controlled,
        lead_to_shot=lead_to_shot
    ))
    
    return {
        "entries": db_entries,
        "total": total_entries,
        "skip": skip,
        "limit": limit
    }


@router.get("/{entry_id}", response_model=EntryWithRelations)
def get_entry(
    entry_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific zone entry by ID.
    """
    db_entry = crud_entries.get_entry_by_id(db, entry_id=entry_id)
    if db_entry is None:
        raise HTTPException(status_code=404, detail="Zone entry not found")
    return db_entry


@router.post("/", response_model=EntryWithRelations)
def create_entry(
    entry: EntryCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new zone entry.
    """
    try:
        return crud_entries.create_entry(db=db, entry=entry)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{entry_id}", response_model=EntryWithRelations)
def update_entry(
    entry_id: int,
    entry: EntryUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a zone entry.
    """
    db_entry = crud_entries.update_entry(db, entry_id=entry_id, entry_update=entry)
    if db_entry is None:
        raise HTTPException(status_code=404, detail="Zone entry not found")
    return db_entry


@router.delete("/{entry_id}")
def delete_entry(
    entry_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a zone entry.
    """
    success = crud_entries.delete_entry(db, entry_id=entry_id)
    if not success:
        raise HTTPException(status_code=404, detail="Zone entry not found")
    return {"status": "success", "message": "Zone entry deleted successfully"}


@router.get("/player/{player_id}/stats", response_model=PlayerEntryStats)
def get_player_entries_stats(
    player_id: str,
    db: Session = Depends(get_db)
):
    """
    Get zone entry statistics for a specific player.
    """
    stats = crud_entries.get_player_entries_stats(db, player_id=player_id)
    if "error" in stats:
        raise HTTPException(status_code=404, detail=stats["error"])
    return stats


@router.get("/team/{team_id}/stats", response_model=TeamEntryStats)
def get_team_entries_stats(
    team_id: str,
    db: Session = Depends(get_db)
):
    """
    Get zone entry statistics for a specific team.
    """
    stats = crud_entries.get_team_entries_stats(db, team_id=team_id)
    if "error" in stats:
        raise HTTPException(status_code=404, detail=stats["error"])
    return stats