from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.team import Team, TeamCreate, TeamUpdate, TeamWithStats, TeamList
from app.crud import teams as crud_teams

router = APIRouter()


@router.get("/", response_model=TeamList)
def get_teams(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get all teams with optional filtering and pagination.
    """
    db_teams = crud_teams.get_teams(db, skip=skip, limit=limit, search=search)
    total = len(crud_teams.get_teams(db, skip=0, limit=None, search=search))
    
    return {
        "teams": db_teams,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/{team_id}", response_model=Team)
def get_team(
    team_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a specific team by team_id.
    """
    db_team = crud_teams.get_team_by_team_id(db, team_id=team_id)
    if db_team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    return db_team


@router.post("/", response_model=Team)
def create_team(
    team: TeamCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new team.
    """
    db_team = crud_teams.get_team_by_team_id(db, team_id=team.team_id)
    if db_team:
        raise HTTPException(status_code=400, detail="Team already exists")
    return crud_teams.create_team(db=db, team=team)


@router.put("/{team_id}", response_model=Team)
def update_team(
    team_id: str,
    team: TeamUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a team.
    """
    db_team = crud_teams.update_team(db, team_id=team_id, team_update=team)
    if db_team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    return db_team


@router.delete("/{team_id}")
def delete_team(
    team_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a team.
    """
    success = crud_teams.delete_team(db, team_id=team_id)
    if not success:
        raise HTTPException(status_code=404, detail="Team not found")
    return {"status": "success", "message": "Team deleted successfully"}


@router.get("/{team_id}/stats", response_model=TeamWithStats)
def get_team_stats(
    team_id: str,
    db: Session = Depends(get_db)
):
    """
    Get statistics for a specific team.
    """
    stats = crud_teams.get_team_stats(db, team_id=team_id)
    if "error" in stats:
        raise HTTPException(status_code=404, detail=stats["error"])
    return stats