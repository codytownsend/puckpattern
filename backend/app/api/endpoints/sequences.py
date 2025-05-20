from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from app.db.session import get_db
from app.services.sequence_service import SequenceService
from app.schemas.sequence import SequenceList
from app.models.analytics import Game
from app.models.base import GameEvent, Team

router = APIRouter()

@router.get("/cycles", response_model=SequenceList)
def get_cycle_sequences(
    game_id: int = Query(..., description="Game ID"),
    team_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Get offensive cycle sequences for a game and team
    """
    sequence_service = SequenceService(db)
    
    # Check if game exists
    game = db.query(Game).filter(Game.game_id == str(game_id)).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    # Get cycles
    cycles = sequence_service.detect_cycles(game_id=str(game_id), team_id=team_id)
    
    # Format cycles for the response
    formatted_cycles = []
    for cycle in cycles:
        # For each cycle, get the events
        cycle_events = []
        team_name = None
        player_ids = []
        
        for pass_event in cycle:
            # Get the basic event
            event = db.query(GameEvent).filter(GameEvent.id == pass_event.event_id).first()
            if not event:
                continue
                
            # Get team name if not already set
            if not team_name and event.team_id:
                team = db.query(Team).filter(Team.id == event.team_id).first()
                if team:
                    team_name = team.name
            
            # Add player to list if not already included
            if event.player_id and event.player_id not in player_ids:
                player_ids.append(event.player_id)
                
            # Add event data
            cycle_events.append({
                "id": event.id,
                "event_type": event.event_type,
                "period": event.period,
                "time_elapsed": event.time_elapsed,
                "coordinates": {
                    "x": event.x_coordinate,
                    "y": event.y_coordinate
                },
                "player": {
                    "id": event.player_id
                } if event.player_id else None
            })
        
        # Only add if we have at least 2 events
        if len(cycle_events) >= 2:
            # Calculate duration
            start_time = cycle_events[0]["time_elapsed"]
            end_time = cycle_events[-1]["time_elapsed"]
            duration = end_time - start_time
            
            # Determine if cycle led to a shot
            shot_resulted = any(e["event_type"] in ["SHOT", "GOAL", "SHOT-ON-GOAL"] for e in cycle_events)
            
            formatted_cycles.append({
                "id": cycle[0].id if cycle else 0,
                "events": cycle_events,
                "duration": duration,
                "zone": "OZ",  # Since cycles are in the offensive zone
                "team_id": team_id or (event.team_id if event else 0),
                "team_name": team_name or "Unknown",
                "player_ids": player_ids,
                "pass_count": len(cycle),
                "shot_resulted": shot_resulted
            })
    
    return {
        "sequences": formatted_cycles,
        "total": len(formatted_cycles),
        "sequence_type": "cycle",
        "game_id": str(game_id),
        "team_id": team_id
    }

@router.get("/rushes", response_model=SequenceList)
def get_rush_plays(
    game_id: int = Query(..., description="Game ID"),
    team_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Get rush play sequences for a game and team
    """
    sequence_service = SequenceService(db)
    
    # Check if game exists
    game = db.query(Game).filter(Game.game_id == str(game_id)).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    # Get rush plays
    rushes = sequence_service.detect_rush_plays(db, str(game_id), team_id)
    
    # Format rushes for the response
    formatted_rushes = []
    for rush in rushes:
        # Skip rushes with fewer than 2 events
        if len(rush) < 2:
            continue
            
        # Get team and player info
        team_id = rush[0].team_id
        team_name = "Unknown"
        if team_id:
            team = db.query(Team).filter(Team.id == team_id).first()
            if team:
                team_name = team.name
                
        # Main player is the one who appears most in the rush
        player_counts = {}
        for event in rush:
            if event.player_id:
                player_counts[event.player_id] = player_counts.get(event.player_id, 0) + 1
        
        primary_player_id = max(player_counts.items(), key=lambda x: x[1])[0] if player_counts else None
        
        # Determine start and end zones
        first_event = rush[0]
        last_event = rush[-1]
        
        start_zone = determine_zone(first_event.x_coordinate)
        end_zone = determine_zone(last_event.x_coordinate)
        
        # Calculate distance covered
        distance_covered = 0
        for i in range(1, len(rush)):
            if rush[i-1].x_coordinate is not None and rush[i-1].y_coordinate is not None and \
               rush[i].x_coordinate is not None and rush[i].y_coordinate is not None:
                dx = rush[i].x_coordinate - rush[i-1].x_coordinate
                dy = rush[i].y_coordinate - rush[i-1].y_coordinate
                distance_covered += (dx**2 + dy**2)**0.5
        
        # Check if rush resulted in a shot or goal
        shot_resulted = any(e.event_type in ["SHOT", "SHOT-ON-GOAL"] for e in rush)
        goal_resulted = any(e.event_type == "GOAL" for e in rush)
        
        # Format events for response
        events = []
        for event in rush:
            events.append({
                "id": event.id,
                "event_type": event.event_type,
                "period": event.period,
                "time_elapsed": event.time_elapsed,
                "coordinates": {
                    "x": event.x_coordinate,
                    "y": event.y_coordinate
                },
                "player": {
                    "id": event.player_id
                } if event.player_id else None
            })
        
        # Add the formatted rush
        formatted_rushes.append({
            "id": rush[0].id,
            "events": events,
            "duration": last_event.time_elapsed - first_event.time_elapsed,
            "start_zone": start_zone,
            "end_zone": end_zone,
            "team_id": team_id or 0,
            "team_name": team_name,
            "primary_player_id": primary_player_id,
            "distance_covered": distance_covered,
            "shot_resulted": shot_resulted,
            "goal_resulted": goal_resulted
        })
    
    return {
        "sequences": formatted_rushes,
        "total": len(formatted_rushes),
        "sequence_type": "rush",
        "game_id": str(game_id),
        "team_id": team_id
    }

def determine_zone(x_coordinate):
    """Determine which zone an x-coordinate falls into."""
    if x_coordinate is None:
        return "NZ"  # Default to neutral zone if None
    elif x_coordinate > 25:
        return "OZ"  # Offensive zone
    elif x_coordinate < -25:
        return "DZ"  # Defensive zone
    else:
        return "NZ"  # Neutral zone