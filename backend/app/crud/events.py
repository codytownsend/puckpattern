from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_, desc, asc

from app.models.base import GameEvent, Team, Player, Game
from app.schemas.event import EventCreate, EventUpdate


def get_events(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    game_id: Optional[int] = None,
    team_id: Optional[int] = None,
    player_id: Optional[int] = None,
    event_type: Optional[str] = None,
    period: Optional[int] = None,
    sort_by: str = "time_elapsed",
    sort_desc: bool = False
) -> List[GameEvent]:
    """
    Get game events with various filters.
    """
    query = db.query(GameEvent).options(
        joinedload(GameEvent.player),
        joinedload(GameEvent.team)
    )
    
    if game_id:
        query = query.filter(GameEvent.game_id == game_id)
    
    if team_id:
        # Get the internal team ID first
        team = db.query(Team).filter(Team.team_id == team_id).first()
        if team:
            query = query.filter(GameEvent.team_id == team.id)
    
    if player_id:
        # Get the internal player ID first
        player = db.query(Player).filter(Player.player_id == player_id).first()
        if player:
            query = query.filter(GameEvent.player_id == player.id)
    
    if event_type:
        query = query.filter(GameEvent.event_type == event_type)
    
    if period:
        query = query.filter(GameEvent.period == period)
    
    # Apply sorting
    if sort_by == "time_elapsed":
        if sort_desc:
            query = query.order_by(desc(GameEvent.period), desc(GameEvent.time_elapsed))
        else:
            query = query.order_by(asc(GameEvent.period), asc(GameEvent.time_elapsed))
    elif sort_by == "period":
        if sort_desc:
            query = query.order_by(desc(GameEvent.period), asc(GameEvent.time_elapsed))
        else:
            query = query.order_by(asc(GameEvent.period), asc(GameEvent.time_elapsed))
    # Add other sorting options as needed
    
    if limit:
        return query.offset(skip).limit(limit).all()
    return query.offset(skip).all()


def get_event_by_id(db: Session, event_id: int) -> Optional[GameEvent]:
    """
    Get a specific event by ID.
    """
    return db.query(GameEvent).options(
        joinedload(GameEvent.player),
        joinedload(GameEvent.team)
    ).filter(GameEvent.id == event_id).first()


def create_event(db: Session, event: EventCreate) -> GameEvent:
    """
    Create a new game event.
    """
    # Get player and team IDs if provided
    player_id = None
    if event.player_id:
        player = db.query(Player).filter(Player.player_id == event.player_id).first()
        if player:
            player_id = player.id
    
    team_id = None
    if event.team_id:
        team = db.query(Team).filter(Team.team_id == event.team_id).first()
        if team:
            team_id = team.id
    
    # Ensure the game exists
    game = db.query(Game).filter(Game.game_id == event.game_id).first()
    if not game:
        raise ValueError(f"Game with ID {event.game_id} not found")
    
    db_event = GameEvent(
        game_id=event.game_id,
        event_type=event.event_type,
        period=event.period,
        time_elapsed=event.time_elapsed,
        x_coordinate=event.x_coordinate,
        y_coordinate=event.y_coordinate,
        player_id=player_id,
        team_id=team_id
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


def update_event(db: Session, event_id: int, event_update: EventUpdate) -> Optional[GameEvent]:
    """
    Update a game event.
    """
    db_event = get_event_by_id(db, event_id)
    if not db_event:
        return None
    
    event_data = event_update.dict(exclude_unset=True)
    
    # Handle player_id and team_id if provided
    if "player_id" in event_data:
        player_id = event_data.pop("player_id")
        if player_id:
            player = db.query(Player).filter(Player.player_id == player_id).first()
            if player:
                event_data["player_id"] = player.id
            else:
                event_data["player_id"] = None
        else:
            event_data["player_id"] = None
    
    if "team_id" in event_data:
        team_id = event_data.pop("team_id")
        if team_id:
            team = db.query(Team).filter(Team.team_id == team_id).first()
            if team:
                event_data["team_id"] = team.id
            else:
                event_data["team_id"] = None
        else:
            event_data["team_id"] = None
    
    for key, value in event_data.items():
        setattr(db_event, key, value)
    
    db.commit()
    db.refresh(db_event)
    return db_event


def delete_event(db: Session, event_id: int) -> bool:
    """
    Delete a game event.
    """
    db_event = get_event_by_id(db, event_id)
    if not db_event:
        return False
    
    db.delete(db_event)
    db.commit()
    return True


def get_game_play_by_play(db: Session, game_id: int) -> List[Dict[str, Any]]:
    """
    Get a chronological play-by-play list of events for a game.
    """
    # First, check if the game exists
    game = db.query(Game).filter(Game.game_id == game_id).first()
    if not game:
        return []
    
    # Get all events for this game
    events = get_events(
        db,
        game_id=game_id,
        sort_by="time_elapsed",
        sort_desc=False,
        limit=None
    )
    
    play_by_play = []
    for event in events:
        # Build a rich event object
        event_data = {
            "id": event.id,
            "event_type": event.event_type,
            "period": event.period,
            "time_elapsed": event.time_elapsed,
            "coordinates": {
                "x": event.x_coordinate,
                "y": event.y_coordinate
            },
            "team": None,
            "player": None,
            # Add more fields as needed
        }
        
        # Add team information if available
        if event.team:
            event_data["team"] = {
                "id": event.team.id,
                "team_id": event.team.team_id,
                "name": event.team.name,
                "abbreviation": event.team.abbreviation
            }
        
        # Add player information if available
        if event.player:
            event_data["player"] = {
                "id": event.player.id,
                "player_id": event.player.player_id,
                "name": event.player.name,
                "position": event.player.position
            }
        
        play_by_play.append(event_data)
    
    return play_by_play