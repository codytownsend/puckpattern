from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.shot import Shot, ShotCreate, ShotResponse, ShotHeatmapResponse
from app.crud import shots as crud_shots
from app.services.shot_analysis import ShotAnalysisService

router = APIRouter()


@router.get("/", response_model=List[ShotResponse])
def get_shots(
    game_id: Optional[int] = None,
    player_id: Optional[int] = None,
    team_id: Optional[int] = None,
    shot_type: Optional[str] = None,
    period: Optional[int] = None,
    is_goal: Optional[bool] = None,
    min_xg: Optional[float] = None,
    max_xg: Optional[float] = None,
    limit: int = 100,
    skip: int = 0,
    db: Session = Depends(get_db)
):
    """
    Get shots with various filters.
    """
    filters = {
        "game_id": game_id,
        "player_id": player_id,
        "team_id": team_id, 
        "shot_type": shot_type,
        "period": period,
        "is_goal": is_goal,
        "min_xg": min_xg,
        "max_xg": max_xg
    }
    return crud_shots.get_shots(db, skip=skip, limit=limit, filters=filters)


@router.post("/", response_model=ShotResponse)
def create_shot(
    shot: ShotCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new shot event.
    """
    return crud_shots.create_shot(db, shot=shot)


@router.get("/heatmap", response_model=ShotHeatmapResponse)
def get_shot_heatmap(
    team_id: Optional[int] = None,
    player_id: Optional[int] = None,
    game_id: Optional[int] = None,
    season: Optional[str] = None,
    shot_type: Optional[str] = None,
    goal_only: bool = False,
    normalize: bool = True,
    db: Session = Depends(get_db)
):
    """
    Get shot heatmap data for visualization.
    """
    shot_service = ShotAnalysisService(db)
    
    filters = {
        "team_id": team_id,
        "player_id": player_id,
        "game_id": game_id,
        "season": season,
        "shot_type": shot_type,
        "goal_only": goal_only
    }
    
    return shot_service.generate_heatmap(filters, normalize)


@router.get("/xg-breakdown", response_model=dict)
def get_xg_breakdown(
    player_id: int,
    season: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get a detailed breakdown of player's expected goals.
    """
    shot_service = ShotAnalysisService(db)
    return shot_service.get_xg_breakdown(player_id, season)


@router.get("/team-comparison", response_model=dict)
def compare_team_shot_patterns(
    team_id1: int,
    team_id2: int,
    season: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Compare shot patterns between two teams.
    """
    shot_service = ShotAnalysisService(db)
    return shot_service.compare_team_shot_patterns(team_id1, team_id2, season)


@router.get("/dangerous-zones/{player_id}", response_model=dict)
def get_player_dangerous_zones(
    player_id: int,
    season: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get zones where a player is most dangerous (highest xG).
    """
    shot_service = ShotAnalysisService(db)
    return shot_service.get_player_dangerous_zones(player_id, season)