from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.player import Player, PlayerCreate, PlayerUpdate, PlayerWithTeam, PlayerWithStats, PlayerList
from app.schemas.analytics import PlayerAnalytics
from app.crud import players as crud_players
from app.crud import entries as crud_entries
from app.services.metrics_service import MetricsService
from app.services.sequence_service import SequenceService

router = APIRouter()


@router.get("/", response_model=PlayerList)
def get_players(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    team_id: Optional[int] = None,
    position: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get all players with optional filtering and pagination.
    """
    db_players = crud_players.get_players(
        db, 
        skip=skip, 
        limit=limit, 
        search=search,
        team_id=team_id,
        position=position
    )
    
    # Get total count for pagination
    total_players = len(crud_players.get_players(
        db, 
        search=search,
        team_id=team_id,
        position=position
    ))
    
    return {
        "players": db_players,
        "total": total_players,
        "skip": skip,
        "limit": limit
    }


@router.get("/{player_id}", response_model=PlayerWithTeam)
def get_player(
    player_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a specific player by player_id.
    """
    db_player = crud_players.get_player_by_player_id(db, player_id=player_id)
    if db_player is None:
        raise HTTPException(status_code=404, detail="Player not found")
    return db_player


@router.post("/", response_model=Player)
def create_player(
    player: PlayerCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new player.
    """
    db_player = crud_players.get_player_by_player_id(db, player_id=player.player_id)
    if db_player:
        raise HTTPException(status_code=400, detail="Player already exists")
    return crud_players.create_player(db=db, player=player)


@router.put("/{player_id}", response_model=Player)
def update_player(
    player_id: int,
    player: PlayerUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a player.
    """
    db_player = crud_players.update_player(db, player_id=player_id, player_update=player)
    if db_player is None:
        raise HTTPException(status_code=404, detail="Player not found")
    return db_player


@router.delete("/{player_id}")
def delete_player(
    player_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a player.
    """
    success = crud_players.delete_player(db, player_id=player_id)
    if not success:
        raise HTTPException(status_code=404, detail="Player not found")
    return {"status": "success", "message": "Player deleted successfully"}


@router.get("/{player_id}/stats", response_model=PlayerWithStats)
def get_player_stats(
    player_id: int,
    season: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get statistics for a specific player.
    """
    stats = crud_players.get_player_stats(db, player_id=player_id)
    if "error" in stats:
        raise HTTPException(status_code=404, detail=stats["error"])
    return stats

@router.get("/{player_id}/analytics", response_model=PlayerAnalytics)
def get_player_analytics(
    player_id: int,
    game_id: Optional[int] = None,
    season: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get comprehensive analytics for a player
    """
    metrics_service = MetricsService(db)
    sequence_service = SequenceService(db)
    
    # Get player
    player = crud_players.get_player_by_player_id(db, player_id=player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    # Calculate metrics
    ecr = metrics_service.calculate_ecr(player_id=player.id, game_id=game_id)
    pri = metrics_service.calculate_pri(player_id=player.id, game_id=game_id)
    pdi = metrics_service.calculate_pdi(player_id=player.id, game_id=game_id)
    xg_delta_psm = metrics_service.calculate_xg_delta_psm(player_id=player.id, game_id=game_id)
    
    # Get shot metrics
    shot_metrics = metrics_service.calculate_shot_metrics(player_id=player.id, game_id=game_id)
    
    # Get zone entries
    entries = crud_entries.get_player_entries_stats(db, player_id=player_id)
    
    # Calculate ICE+ score
    ice_plus = (ecr * 1.5) + (pri * 1.2) + (pdi * 1.0) + (xg_delta_psm * 2.0)
    
    return {
        "player_id": player_id,
        "name": player.name,
        "team": {
            "id": player.team.id,
            "team_id": player.team.team_id,
            "name": player.team.name,
            "abbreviation": player.team.abbreviation
        } if player.team else None,
        "position": player.position,
        "ecr": ecr,
        "pri": pri,
        "pdi": pdi,
        "xg_delta_psm": xg_delta_psm,
        "shot_metrics": shot_metrics,
        "entries": entries,
        "ice_plus": ice_plus
    }