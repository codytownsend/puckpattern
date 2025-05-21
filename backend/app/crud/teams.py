from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_

from app.models.base import Player, Team
from app.schemas.team import TeamCreate, TeamUpdate


def get_teams(
    db: Session, 
    skip: int = 0, 
    limit: Optional[int] = 100,
    search: Optional[str] = None,
    conference: Optional[str] = None,
    division: Optional[str] = None
) -> List[Team]:
    """
    Get all teams with optional search by name or abbreviation.
    """
    query = db.query(Team)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Team.name.ilike(search_term),
                Team.abbreviation.ilike(search_term),
                Team.city_name.ilike(search_term)
            )
        )
    
    if conference:
        query = query.filter(Team.conference == conference)
    
    if division:
        query = query.filter(Team.division == division)
    
    if limit:
        return query.offset(skip).limit(limit).all()
    return query.offset(skip).all()


def get_team_by_id(db: Session, team_id: int) -> Optional[Team]:
    """
    Get a team by internal ID.
    """
    return db.query(Team).filter(Team.id == team_id).first()


def get_team_by_team_id(db: Session, team_id: int) -> Optional[Team]:
    """
    Get a team by external team_id (e.g., NHL API ID).
    """
    return db.query(Team).filter(Team.team_id == str(team_id)).first()


def get_team_by_abbreviation(db: Session, abbreviation: str) -> Optional[Team]:
    """
    Get a team by its abbreviation (e.g., "TOR", "EDM").
    """
    return db.query(Team).filter(Team.abbreviation == abbreviation).first()


def create_team(db: Session, team: TeamCreate) -> Team:
    """
    Create a new team.
    """
    db_team = Team(
        team_id=team.team_id,
        name=team.name,
        abbreviation=team.abbreviation,
        city_name=team.city_name,
        team_name=team.team_name,
        division=team.division,
        conference=team.conference,
        venue_name=team.venue_name,
        venue_city=team.venue_city,
        official_site_url=team.official_site_url,
        active=team.active
    )
    db.add(db_team)
    db.commit()
    db.refresh(db_team)
    return db_team


def update_team(db: Session, team_id: int, team_update: TeamUpdate) -> Optional[Team]:
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


def delete_team(db: Session, team_id: int) -> bool:
    """
    Delete a team by team_id.
    """
    db_team = get_team_by_team_id(db, team_id)
    if not db_team:
        return False
    
    db.delete(db_team)
    db.commit()
    return True


def get_team_stats(db: Session, team_id: int) -> Dict[str, Any]:
    """
    Get basic stats for a team.
    """
    db_team = get_team_by_team_id(db, team_id)
    if not db_team:
        return {"error": "Team not found"}
    
    # Count number of players associated with the team
    player_count = db.query(func.count(Player.id)).filter(Player.team_id == db_team.id).scalar()
    
    # Get team games
    from app.models.analytics import Game
    games = db.query(Game).filter(
        (Game.home_team_id == db_team.id) | (Game.away_team_id == db_team.id)
    ).all()
    
    games_played = len(games) if games else 0
    wins = 0
    losses = 0
    overtime_losses = 0
    goals_for = 0
    goals_against = 0
    
    # Calculate basic statistics
    for game in games:
        if game.status != "FINAL":
            continue
            
        if game.home_team_id == db_team.id:
            goals_for += game.home_score or 0
            goals_against += game.away_score or 0
            if game.home_score > game.away_score:
                wins += 1
            elif game.home_score < game.away_score:
                if game.period > 3:  # Overtime loss
                    overtime_losses += 1
                else:
                    losses += 1
        else:  # Away team
            goals_for += game.away_score or 0
            goals_against += game.home_score or 0
            if game.away_score > game.home_score:
                wins += 1
            elif game.away_score < game.home_score:
                if game.period > 3:  # Overtime loss
                    overtime_losses += 1
                else:
                    losses += 1
    
    # Get additional statistics from TeamGameStats if available
    from app.models.analytics import TeamGameStats
    team_game_stats = db.query(TeamGameStats).filter(TeamGameStats.team_id == db_team.id).all()
    
    xg_for = sum(stats.xg for stats in team_game_stats) if team_game_stats else None
    xg_against = sum(stats.xg_against for stats in team_game_stats) if team_game_stats else None
    
    # Compile system metrics if available
    system_metrics = {}
    if team_game_stats:
        # Get most common forecheck style
        forecheck_styles = [stats.forecheck_style for stats in team_game_stats if stats.forecheck_style]
        if forecheck_styles:
            from collections import Counter
            system_metrics["forecheck_style"] = Counter(forecheck_styles).most_common(1)[0][0]
        
        # Get most common defensive structure
        defensive_structures = [stats.defensive_structure for stats in team_game_stats if stats.defensive_structure]
        if defensive_structures:
            from collections import Counter
            system_metrics["defensive_structure"] = Counter(defensive_structures).most_common(1)[0][0]
        
        # Get most common PP formation
        pp_formations = [stats.pp_formation for stats in team_game_stats if stats.pp_formation]
        if pp_formations:
            from collections import Counter
            system_metrics["pp_formation"] = Counter(pp_formations).most_common(1)[0][0]
        
        # Get most common PK formation
        pk_formations = [stats.pk_formation for stats in team_game_stats if stats.pk_formation]
        if pk_formations:
            from collections import Counter
            system_metrics["pk_formation"] = Counter(pk_formations).most_common(1)[0][0]
    
    return {
        "id": db_team.id,
        "team_id": db_team.team_id,
        "name": db_team.name,
        "abbreviation": db_team.abbreviation,
        "conference": db_team.conference,
        "division": db_team.division,
        "city_name": db_team.city_name,
        "team_name": db_team.team_name,
        "venue_name": db_team.venue_name,
        "venue_city": db_team.venue_city,
        "player_count": player_count,
        "games_played": games_played,
        "wins": wins,
        "losses": losses,
        "overtime_losses": overtime_losses,
        "points": (wins * 2) + overtime_losses,
        "goals_for": goals_for,
        "goals_against": goals_against,
        "xg_for": xg_for,
        "xg_against": xg_against,
        "system_metrics": system_metrics if system_metrics else None
    }