from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.event import Event, EventCreate, EventUpdate, EventWithRelations, PlayByPlayEvent, EventList
from app.crud import events as crud_events

router = APIRouter()


@router.get("/", response_model=EventList)
def get_events(
    skip: int = 0,
    limit: int = 100,
    game_id: Optional[str] = None,
    team_id: Optional[str] = None,
    player_id: Optional[str] = None,
    event_type: Optional[str] = None,
    period: Optional[int] = None,
    sort_by: str = "time_elapsed",
    sort_desc: bool = False,
    db: Session = Depends(get_db)
):
    """
    Get all game events with optional filtering and pagination.
    """
    db_events = crud_events.get_events(
        db, 
        skip=skip, 
        limit=limit, 
        game_id=game_id,
        team_id=team_id,
        player_id=player_id,
        event_type=event_type,
        period=period,
        sort_by=sort_by,
        sort_desc=sort_desc
    )
    
    # Get total count for pagination
    total_events = len(crud_events.get_events(
        db, 
        game_id=game_id,
        team_id=team_id,
        player_id=player_id,
        event_type=event_type,
        period=period
    ))
    
    return {
        "events": db_events,
        "total": total_events,
        "skip": skip,
        "limit": limit
    }


@router.get("/{event_id}", response_model=EventWithRelations)
def get_event(
    event_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific game event by ID.
    """
    db_event = crud_events.get_event_by_id(db, event_id=event_id)
    if db_event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return db_event


@router.post("/", response_model=EventWithRelations)
def create_event(
    event: EventCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new game event.
    """
    try:
        return crud_events.create_event(db=db, event=event)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{event_id}", response_model=EventWithRelations)
def update_event(
    event_id: int,
    event: EventUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a game event.
    """
    db_event = crud_events.update_event(db, event_id=event_id, event_update=event)
    if db_event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return db_event


@router.delete("/{event_id}")
def delete_event(
    event_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a game event.
    """
    success = crud_events.delete_event(db, event_id=event_id)
    if not success:
        raise HTTPException(status_code=404, detail="Event not found")
    return {"status": "success", "message": "Event deleted successfully"}


@router.get("/game/{game_id}/play-by-play", response_model=List[PlayByPlayEvent])
def get_game_play_by_play(
    game_id: str,
    db: Session = Depends(get_db)
):
    """
    Get chronological play-by-play events for a specific game.
    """
    play_by_play = crud_events.get_game_play_by_play(db, game_id=game_id)
    if not play_by_play:
        raise HTTPException(status_code=404, detail="Game not found or no events recorded")
    return play_by_play