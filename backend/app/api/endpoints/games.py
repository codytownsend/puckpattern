from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.game import Game, GameCreate, GameUpdate, GameWithTeams, GameWithStats, GameList
from app.crud import games as crud_games

router = APIRouter()


@router.get("/", response_model=GameList)
def get_games(
    skip: int = 0,
    limit: int = 100,
    season: Optional[str] = None,
    team_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    status: Optional[str] = None,
    sort_by: str = "date",
    sort_desc: bool = True,
    db: Session = Depends(get_db)
):
    """
    Get all games with optional filtering and pagination.
    """
    db_games = crud_games.get_games(
        db, 
        skip=skip, 
        limit=limit, 
        season=season,
        team_id=team_id,
        start_date=start_date,
        end_date=end_date,
        status=status,
        sort_by=sort_by,
        sort_desc=sort_desc
    )
    
    # Get total count for pagination
    total_games = len(crud_games.get_games(
        db, 
        season=season,
        team_id=team_id,
        start_date=start_date,
        end_date=end_date,
        status=status,
        sort_by=sort_by,
        sort_desc=sort_desc
    ))
    
    return {
        "games": db_games,
        "total": total_games,
        "skip": skip,
        "limit": limit
    }


@router.get("/{game_id}", response_model=GameWithTeams)
def get_game(
    game_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific game by game_id.
    """
    db_game = crud_games.get_game_by_game_id(db, game_id=game_id)
    if db_game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return db_game


@router.post("/", response_model=GameWithTeams)
def create_game(
    game: GameCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new game.
    """
    try:
        db_game = crud_games.get_game_by_game_id(db, game_id=game.game_id)
        if db_game:
            raise HTTPException(status_code=400, detail="Game already exists")
        return crud_games.create_game(db=db, game=game)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{game_id}", response_model=GameWithTeams)
def update_game(
    game_id: int,
    game: GameUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a game.
    """
    db_game = crud_games.update_game(db, game_id=game_id, game_update=game)
    if db_game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return db_game


@router.delete("/{game_id}")
def delete_game(
    game_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a game.
    """
    success = crud_games.delete_game(db, game_id=game_id)
    if not success:
        raise HTTPException(status_code=404, detail="Game not found")
    return {"status": "success", "message": "Game deleted successfully"}


@router.get("/{game_id}/stats", response_model=GameWithStats)
def get_game_stats(
    game_id: int,
    db: Session = Depends(get_db)
):
    """
    Get detailed statistics for a specific game.
    """
    stats = crud_games.get_game_stats(db, game_id=game_id)
    if "error" in stats:
        raise HTTPException(status_code=404, detail=stats["error"])
    return stats