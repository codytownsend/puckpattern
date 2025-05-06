from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_

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
        position=player.position,
        sweater_number=player.sweater_number,
        player_slug=player.player_slug,
        height_in_inches=player.height_in_inches,
        height_in_cm=player.height_in_cm,
        weight_in_pounds=player.weight_in_pounds,
        weight_in_kg=player.weight_in_kg,
        birth_date=player.birth_date,
        birth_city=player.birth_city,
        birth_state_province=player.birth_state_province,
        birth_country=player.birth_country,
        shoots_catches=player.shoots_catches,
        headshot_url=player.headshot_url
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


def get_player_stats(db: Session, player_id: str, season: Optional[str] = None) -> Dict[str, Any]:
    """
    Get statistics for a player.
    """
    db_player = get_player_by_player_id(db, player_id)
    if not db_player:
        return {"error": "Player not found"}
    
    # Get team info if available
    team_info = None
    if db_player.team_id:
        team = db.query(Team).filter(Team.id == db_player.team_id).first()
        if team:
            team_info = {
                "id": team.id,
                "team_id": team.team_id,
                "name": team.name,
                "abbreviation": team.abbreviation,
                "conference": team.conference,
                "division": team.division
            }
    
    # Get player game stats
    from app.models.analytics import Game, PlayerGameStats
    
    query = db.query(PlayerGameStats).filter(PlayerGameStats.player_id == db_player.id)
    
    if season:
        query = query.join(Game, PlayerGameStats.game_id == Game.id).filter(Game.season == season)
    
    player_game_stats = query.all()
    
    # Calculate totals from game stats
    games_played = len(player_game_stats)
    
    # Basic stats
    goals = sum(stats.goals for stats in player_game_stats) if player_game_stats else 0
    assists = sum(stats.assists for stats in player_game_stats) if player_game_stats else 0
    points = goals + assists
    shots = sum(stats.shots for stats in player_game_stats) if player_game_stats else 0
    shot_percentage = (goals / shots * 100) if shots > 0 else 0.0
    
    # Advanced stats
    xg = sum(stats.xg for stats in player_game_stats) if player_game_stats else None
    xg_per_game = (xg / games_played) if xg is not None and games_played > 0 else None
    
    # Get power play stats
    pp_goals = sum(stats.pp_goals for stats in player_game_stats) if player_game_stats else 0
    pp_assists = sum(stats.pp_assists for stats in player_game_stats) if player_game_stats else 0
    pp_points = pp_goals + pp_assists
    
    # Get face-off stats
    faceoffs_taken = sum(stats.faceoffs_taken for stats in player_game_stats) if player_game_stats else 0
    faceoffs_won = sum(stats.faceoffs_won for stats in player_game_stats) if player_game_stats else 0
    face_off_pct = (faceoffs_won / faceoffs_taken * 100) if faceoffs_taken > 0 else None
    
    # Get custom metrics
    ecr_values = [stats.ecr for stats in player_game_stats if stats.ecr is not None]
    ecr = sum(ecr_values) / len(ecr_values) if ecr_values else None
    
    pri_values = [stats.pri for stats in player_game_stats if stats.pri is not None]
    pri = sum(pri_values) / len(pri_values) if pri_values else None
    
    pdi_values = [stats.pdi for stats in player_game_stats if stats.pdi is not None]
    pdi = sum(pdi_values) / len(pdi_values) if pdi_values else None
    
    xg_delta_psm_values = [stats.xg_delta_psm for stats in player_game_stats if stats.xg_delta_psm is not None]
    xg_delta_psm = sum(xg_delta_psm_values) / len(xg_delta_psm_values) if xg_delta_psm_values else None
    
    sfs_values = [stats.sfs for stats in player_game_stats if stats.sfs is not None]
    sfs = sum(sfs_values) / len(sfs_values) if sfs_values else None
    
    omc_values = [stats.omc for stats in player_game_stats if stats.omc is not None]
    omc = sum(omc_values) / len(omc_values) if omc_values else None
    
    ice_plus_values = [stats.ice_plus for stats in player_game_stats if stats.ice_plus is not None]
    ice_plus = sum(ice_plus_values) / len(ice_plus_values) if ice_plus_values else None
    
    return {
        "id": db_player.id,
        "player_id": db_player.player_id,
        "name": db_player.name,
        "position": db_player.position,
        "sweater_number": db_player.sweater_number,
        "team": team_info,
        "games_played": games_played,
        "goals": goals,
        "assists": assists,
        "points": points,
        "shots": shots,
        "shot_percentage": shot_percentage,
        "xg": xg,
        "xg_per_game": xg_per_game,
        "pp_goals": pp_goals,
        "pp_assists": pp_assists,
        "pp_points": pp_points,
        "face_off_pct": face_off_pct,
        "ecr": ecr,
        "pri": pri,
        "pdi": pdi,
        "xg_delta_psm": xg_delta_psm,
        "sfs": sfs,
        "omc": omc,
        "ice_plus": ice_plus
    }