from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.sequence_service import SequenceService
from app.schemas.sequence import CycleSequence, RushPlay, SequenceList

# Create the router
router = APIRouter()

@router.get("/cycles", response_model=SequenceList)
def get_cycle_sequences(
    game_id: int,
    team_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Get offensive cycle sequences for a game and team
    """
    sequence_service = SequenceService(db)
    
    # Check if game exists
    from app.models.analytics import Game
    game = db.query(Game).filter(Game.game_id == str(game_id)).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    # Get cycles
    cycles = sequence_service.detect_cycles(game_id=game_id, team_id=team_id)
    
    return {
        "sequences": cycles,
        "total": len(cycles),
        "sequence_type": "cycle"
    }

@router.get("/rushes", response_model=SequenceList)
def get_rush_plays(
    game_id: int,
    team_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Get rush play sequences for a game and team
    """
    sequence_service = SequenceService(db)
    
    # Check if game exists
    from app.models.analytics import Game
    game = db.query(Game).filter(Game.game_id == str(game_id)).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    # Get rush plays
    rushes = sequence_service.detect_rush_plays(game_id=game_id, team_id=team_id)
    
    return {
        "sequences": rushes,
        "total": len(rushes),
        "sequence_type": "rush"
    }