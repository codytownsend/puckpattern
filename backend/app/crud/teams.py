from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.models.base import Team
from app.schemas.team import TeamCreate, TeamUpdate


def get_teams(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    search: Optional[str] = None
) -> List[Team]:
    """
    Get all teams with optional search by name or abbreviation.
    """
    query = db.query(Team)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Team.name.ilike(search_term)) | 
            (Team.abbreviation.ilike(search_term))
        )
    
    return query.offset(skip).limit(limit).all()


def get_team_by_id(db: Session, team_id: int) -> Optional[Team]:
    """
    Get a team by internal ID.
    """
    return db.query(Team).filter(Team.id == team_id).first()


def get_team_by_team_id(db: Session, team_id: str) -> Optional[Team]:
    """
    Get a team by external team_id (e.g., NHL API ID).
    """
    return db.query(Team).filter(Team.team_id == team_id).first()


def create_team(db: Session, team: TeamCreate) -> Team:
    """
    Create a new team.
    """
    db_team = Team(
        team_id=team.team_id,
        name=team.name,
        abbreviation=team.abbreviation
    )
    db.add(db_team)
    db.commit()
    db.refresh(db_team)
    return db_team


def update_team(db: Session, team_id: str, team_update: TeamUpdate) -> Optional[Team]:
    """
    Update a team by team_id.
    """
    db_team = get_team_by_team_id(db, team_id)
    if not db_team:
        return None
    
    team_data = team_update.dict(exclude_unset=True)
    for key, value in team_data.items():
        setattr(db_team, key, value)
    
    db.commit()
    db.refresh(db_team)
    return db_team


def delete_team(db: Session, team_id: str) -> bool:
    """
    Delete a team by team_id.
    """
    db_team = get_team_by_team_id(db, team_id)
    if not db_team:
        return False
    
    db.delete(db_team)
    db.commit()
    return True


def get_team_stats(db: Session, team_id: str) -> Dict[str, Any]:
    """
    Get basic stats for a team.
    """
    db_team = get_team_by_team_id(db, team_id)
    if not db_team:
        return {"error": "Team not found"}
    
    # Count number of players associated with the team
    player_count = db.query(func.count()).filter_by(team_id=db_team.id).scalar()
    
    # You would add more stats here as needed
    
    return {
        "id": db_team.id,
        "team_id": db_team.team_id,
        "name": db_team.name,
        "abbreviation": db_team.abbreviation,
        "player_count": player_count,
        # Add other stats as needed
    }