from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func

from app.models.base import GameEvent, Team, Player, Game
from app.models.analytics import ShotEvent
from app.schemas.shot import ShotCreate


def get_shots(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    filters: Optional[Dict[str, Any]] = None
) -> List[ShotEvent]:
    """
    Get shots with various filters.
    """
    query = db.query(ShotEvent).options(
        joinedload(ShotEvent.event),
        joinedload(ShotEvent.shooter),
        joinedload(ShotEvent.goalie),
        joinedload(ShotEvent.primary_assist),
        joinedload(ShotEvent.secondary_assist)
    )
    
    if filters:
        if filters.get("game_id"):
            query = query.join(GameEvent).filter(GameEvent.game_id == filters["game_id"])
        
        if filters.get("player_id"):
            query = query.filter(
                or_(
                    ShotEvent.shooter_id == filters["player_id"],
                    ShotEvent.primary_assist_id == filters["player_id"],
                    ShotEvent.secondary_assist_id == filters["player_id"]
                )
            )
        
        if filters.get("team_id"):
            query = query.join(GameEvent).filter(GameEvent.team_id == filters["team_id"])
        
        if filters.get("shot_type"):
            query = query.filter(ShotEvent.shot_type == filters["shot_type"])
        
        if filters.get("period"):
            query = query.join(GameEvent).filter(GameEvent.period == filters["period"])
        
        if filters.get("is_goal") is not None:
            query = query.filter(ShotEvent.goal == filters["is_goal"])
        
        if filters.get("min_xg") is not None:
            query = query.filter(ShotEvent.xg >= filters["min_xg"])
        
        if filters.get("max_xg") is not None:
            query = query.filter(ShotEvent.xg <= filters["max_xg"])
    
    return query.offset(skip).limit(limit).all()


def get_shot_by_id(db: Session, shot_id: int) -> Optional[ShotEvent]:
    """
    Get a shot by ID.
    """
    return db.query(ShotEvent).filter(ShotEvent.id == shot_id).first()


def create_shot(db: Session, shot: ShotCreate) -> ShotEvent:
    """
    Create a new shot event.
    """
    # First, find the relevant IDs
    shooter = db.query(Player).filter(Player.player_id == shot.shooter_id).first()
    team = db.query(Team).filter(Team.team_id == shot.team_id).first()
    
    if not shooter or not team:
        raise ValueError("Shooter or team not found")
    
    # Create game event first
    game_event = GameEvent(
        game_id=shot.game_id,
        event_type="SHOT",
        period=shot.period,
        time_elapsed=shot.time_elapsed,
        x_coordinate=shot.x_coordinate,
        y_coordinate=shot.y_coordinate,
        player_id=shooter.id,
        team_id=team.id
    )
    db.add(game_event)
    db.flush()  # Get the ID
    
    # Now create the shot event
    shot_dict = shot.dict(exclude={"game_id", "shooter_id", "team_id"})
    
    # Handle optional relationships
    goalie_id = None
    primary_assist_id = None
    secondary_assist_id = None
    
    if shot.goalie_id:
        goalie = db.query(Player).filter(Player.player_id == shot.goalie_id).first()
        if goalie:
            goalie_id = goalie.id
    
    if shot.primary_assist_id:
        primary_assist = db.query(Player).filter(Player.player_id == shot.primary_assist_id).first()
        if primary_assist:
            primary_assist_id = primary_assist.id
    
    if shot.secondary_assist_id:
        secondary_assist = db.query(Player).filter(Player.player_id == shot.secondary_assist_id).first()
        if secondary_assist:
            secondary_assist_id = secondary_assist.id
    
    # Create shot with calculated fields
    new_shot = ShotEvent(
        event_id=game_event.id,
        shooter_id=shooter.id,
        goalie_id=goalie_id,
        primary_assist_id=primary_assist_id,
        secondary_assist_id=secondary_assist_id,
        preceding_event_id=shot.preceding_event_id,
        **shot_dict
    )
    
    # Calculate xG - This would normally call your xG model
    distance = shot_dict.get("distance")
    angle = shot_dict.get("angle")
    shot_type = shot_dict.get("shot_type")
    
    # Simplified xG calculation for now - will be replaced with actual xG model
    if distance and angle:
        # Simple formula: base xG decreases with distance, modified by angle
        # Will be replaced with a proper xG model in production
        xg_base = max(0.01, 1.0 - (distance / 100))
        angle_factor = abs(angle) / 90.0  # Normalize to 0-1
        new_shot.xg = xg_base * (1.0 - (angle_factor * 0.7))
        
        # Adjust for shot type
        if shot_type == "SLAP_SHOT":
            new_shot.xg *= 0.8
        elif shot_type == "WRIST_SHOT":
            new_shot.xg *= 1.1
        elif shot_type == "DEFLECTION":
            new_shot.xg *= 1.3
        elif shot_type == "ONE_TIMER":
            new_shot.xg *= 1.2
    
    db.add(new_shot)
    db.commit()
    db.refresh(new_shot)
    return new_shot


def update_shot(db: Session, shot_id: int, shot_data: Dict[str, Any]) -> Optional[ShotEvent]:
    """
    Update a shot event.
    """
    shot = db.query(ShotEvent).filter(ShotEvent.id == shot_id).first()
    if not shot:
        return None
    
    for key, value in shot_data.items():
        setattr(shot, key, value)
    
    db.commit()
    db.refresh(shot)
    return shot


def delete_shot(db: Session, shot_id: int) -> bool:
    """
    Delete a shot event.
    """
    shot = db.query(ShotEvent).filter(ShotEvent.id == shot_id).first()
    if not shot:
        return False
    
    # Delete the related game event first
    event = db.query(GameEvent).filter(GameEvent.id == shot.event_id).first()
    if event:
        db.delete(event)
    
    db.delete(shot)
    db.commit()
    return True