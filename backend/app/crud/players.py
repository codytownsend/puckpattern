from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.models.base import Player, Team
from app.schemas.player import PlayerCreate, PlayerUpdate


def get_players(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    search: Optional[str] = None,
    team_id: Optional[str] = None,
    position: Optional[str] = None
) -> List[Player]:
    """
    Get all players with optional filters.
    """
    query = db.query(Player)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(Player.name.ilike(search_term))
    
    if team_id:
        team = db.query(Team).filter(Team.team_id == team_id).first()
        if team:
            query = query.filter(Player.team_id == team.id)
    
    if position:
        query = query.filter(Player.position == position)
    
    return query.offset(skip).limit(limit).all()


def get_player_by_id(db: Session, player_id: int) -> Optional[Player]:
    """
    Get a player by internal ID.
    """
    return db.query(Player).filter(Player.id == player_id).first()


def get_player_by_player_id(db: Session, player_id: str) -> Optional[Player]:
    """
    Get a player by external player_id (e.g., NHL API ID).
    """
    return db.query(Player).filter(Player.player_id == player_id).first()


def create_player(db: Session, player: PlayerCreate) -> Player:
    """
    Create a new player.
    """
    # Get team by team_id if provided
    team_id = None
    if player.team_id:
        team = db.query(Team).filter(Team.team_id == player.team_id).first()
        if team:
            team_id = team.id
    
    db_player = Player(
        player_id=player.player_id,
        name=player.name,
        team_id=team_id,
        position=player.position
    )
    db.add(db_player)
    db.commit()
    db.refresh(db_player)
    return db_player


def update_player(db: Session, player_id: str, player_update: PlayerUpdate) -> Optional[Player]:
    """
    Update a player by player_id.
    """
    db_player = get_player_by_player_id(db, player_id)
    if not db_player:
        return None
    
    player_data = player_update.dict(exclude_unset=True)
    
    # Handle team_id update if provided
    if "team_id" in player_data:
        team_id = player_data.pop("team_id")
        if team_id:
            team = db.query(Team).filter(Team.team_id == team_id).first()
            if team:
                player_data["team_id"] = team.id
            else:
                player_data["team_id"] = None
        else:
            player_data["team_id"] = None
    
    for key, value in player_data.items():
        setattr(db_player, key, value)
    
    db.commit()
    db.refresh(db_player)
    return db_player


def delete_player(db: Session, player_id: str) -> bool:
    """
    Delete a player by player_id.
    """
    db_player = get_player_by_player_id(db, player_id)
    if not db_player:
        return False
    
    db.delete(db_player)
    db.commit()
    return True


def get_player_stats(db: Session, player_id: str) -> Dict[str, Any]:
    """
    Get statistics for a player.
    """
    db_player = get_player_by_player_id(db, player_id)
    if not db_player:
        return {"error": "Player not found"}
    
    # In a real implementation, you would query various stats from game_events, etc.
    # For now, just return basic player info
    
    # Get team info if available
    team_info = None
    if db_player.team_id:
        team = db.query(Team).filter(Team.id == db_player.team_id).first()
        if team:
            team_info = {
                "id": team.id,
                "team_id": team.team_id,
                "name": team.name,
                "abbreviation": team.abbreviation
            }
    
    return {
        "id": db_player.id,
        "player_id": db_player.player_id,
        "name": db_player.name,
        "position": db_player.position,
        "team": team_info,
        # In a real app, you would add other statistics here
        "games_played": 0,
        "goals": 0,
        "assists": 0,
        "points": 0,
        "shots": 0,
        "shot_percentage": 0.0,
        "xg": 0.0,
        "ice_plus": None
    }