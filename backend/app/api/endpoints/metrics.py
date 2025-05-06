from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.metrics import PlayerMetrics, TeamMetrics, MetricValue
from app.services.metrics_service import MetricsService

router = APIRouter()


@router.get("/player/{player_id}", response_model=PlayerMetrics)
def get_player_metrics(
    player_id: int,
    db: Session = Depends(get_db)
):
    """
    Get comprehensive metrics for a specific player.
    """
    metrics_service = MetricsService(db)
    metrics = metrics_service.calculate_player_metrics(player_id)
    
    if "error" in metrics:
        raise HTTPException(status_code=404, detail=metrics["error"])
    
    return metrics


@router.get("/team/{team_id}", response_model=TeamMetrics)
def get_team_metrics(
    team_id: int,
    db: Session = Depends(get_db)
):
    """
    Get comprehensive metrics for a specific team.
    """
    metrics_service = MetricsService(db)
    metrics = metrics_service.calculate_team_metrics(team_id)
    
    if "error" in metrics:
        raise HTTPException(status_code=404, detail=metrics["error"])
    
    return metrics


@router.get("/player/{player_id}/ecr", response_model=MetricValue)
def get_player_ecr(
    player_id: int,
    db: Session = Depends(get_db)
):
    """
    Get Entry Conversion Rate (ECR) for a specific player.
    """
    metrics_service = MetricsService(db)
    
    # Get player
    from app.models.base import Player
    player = db.query(Player).filter(Player.player_id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    # Calculate ECR
    ecr = metrics_service.calculate_ecr(player_id=player.id)
    
    return {
        "name": "Entry Conversion Rate (ECR)",
        "value": ecr,
        "description": "Percentage of controlled zone entries that lead to a shot or scoring chance within 10 seconds"
    }


@router.get("/player/{player_id}/pri", response_model=MetricValue)
def get_player_pri(
    player_id: int,
    db: Session = Depends(get_db)
):
    """
    Get Puck Recovery Impact (PRI) for a specific player.
    """
    metrics_service = MetricsService(db)
    
    # Get player
    from app.models.base import Player
    player = db.query(Player).filter(Player.player_id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    # Calculate PRI
    pri = metrics_service.calculate_pri(player_id=player.id)
    
    return {
        "name": "Puck Recovery Impact (PRI)",
        "value": pri,
        "description": "Weighted sum of puck recoveries based on zone, outcome, and type"
    }


@router.get("/team/{team_id}/ecr", response_model=MetricValue)
def get_team_ecr(
    team_id: int,
    db: Session = Depends(get_db)
):
    """
    Get Entry Conversion Rate (ECR) for a specific team.
    """
    metrics_service = MetricsService(db)
    
    # Get team
    from app.models.base import Team
    team = db.query(Team).filter(Team.team_id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Calculate ECR
    ecr = metrics_service.calculate_ecr(team_id=team.id)
    
    return {
        "name": "Entry Conversion Rate (ECR)",
        "value": ecr,
        "description": "Percentage of controlled zone entries that lead to a shot or scoring chance within 10 seconds"
    }


@router.get("/team/{team_id}/pri", response_model=MetricValue)
def get_team_pri(
    team_id: int,
    db: Session = Depends(get_db)
):
    """
    Get Puck Recovery Impact (PRI) for a specific team.
    """
    metrics_service = MetricsService(db)
    
    # Get team
    from app.models.base import Team
    team = db.query(Team).filter(Team.team_id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Calculate PRI
    pri = metrics_service.calculate_pri(team_id=team.id)
    
    return {
        "name": "Puck Recovery Impact (PRI)",
        "value": pri,
        "description": "Weighted sum of puck recoveries based on zone, outcome, and type"
    }


@router.get("/game/{game_id}/team/{team_id}", response_model=dict)
def get_game_team_metrics(
    game_id: int,
    team_id: int,
    db: Session = Depends(get_db)
):
    """
    Get metrics for a specific team in a specific game.
    """
    metrics_service = MetricsService(db)
    
    # Get team and game
    from app.models.base import Team, Game
    team = db.query(Team).filter(Team.team_id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    game = db.query(Game).filter(Game.game_id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    # Calculate metrics
    ecr = metrics_service.calculate_ecr(team_id=team.id, game_id=game.id)
    pri = metrics_service.calculate_pri(team_id=team.id, game_id=game.id)
    shot_metrics = metrics_service.calculate_shot_metrics(team_id=team.id, game_id=game.id)
    
    return {
        "team_id": team_id,
        "game_id": game_id,
        "ecr": ecr,
        "pri": pri,
        "shot_metrics": shot_metrics
    }