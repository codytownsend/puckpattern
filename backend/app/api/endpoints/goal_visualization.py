from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.goal_visualization_service import GoalVisualizationService
from app.schemas.goal_visualization import GoalVisualization

router = APIRouter()

@router.get("/{goal_id}", response_model=GoalVisualization)
def get_goal_visualization(
    goal_id: str,
    db: Session = Depends(get_db)
):
    """
    Get visualization data for a specific goal.
    """
    visualization_service = GoalVisualizationService(db)
    result = visualization_service.get_goal_visualization(goal_id)
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result