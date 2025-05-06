from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.player import Player, PlayerCreate, PlayerUpdate, PlayerWithTeam, PlayerWithStats, PlayerList
from app.crud import players as crud_players

router = APIRouter()


@router.get("/", response_model=PlayerList)
def get_players(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    team_id: Optional[str] = None,
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
    player_id: str,
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
    player_id: str,
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
    player_id: str,
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