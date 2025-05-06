from typing import Dict, List, Optional, Any
from datetime import datetime, date
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_, desc, asc

from app.models.base import Game, Team
from app.models.analytics import TeamGameStats, PlayerGameStats
from app.schemas.game import GameCreate, GameUpdate


def get_games(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    season: Optional[str] = None,
    team_id: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    status: Optional[str] = None,
    sort_by: str = "date",
    sort_desc: bool = True
) -> List[Game]:
    """
    Get games with various filters.
    """
    query = db.query(Game).options(
        joinedload(Game.home_team),
        joinedload(Game.away_team)
    )
    
    if season:
        query = query.filter(Game.season == season)
    
    if team_id:
        # Get the internal team ID first
        team = db.query(Team).filter(Team.team_id == team_id).first()
        if team:
            # Find games where this team is either home or away
            query = query.filter(
                or_(
                    Game.home_team_id == team.id,
                    Game.away_team_id == team.id
                )
            )
    
    if start_date:
        query = query.filter(func.date(Game.date) >= start_date)
    
    if end_date:
        query = query.filter(func.date(Game.date) <= end_date)
    
    if status:
        query = query.filter(Game.status == status)
    
    # Apply sorting
    if sort_by == "date":
        if sort_desc:
            query = query.order_by(desc(Game.date))
        else:
            query = query.order_by(asc(Game.date))
    elif sort_by == "home_score":
        if sort_desc:
            query = query.order_by(desc(Game.home_score))
        else:
            query = query.order_by(asc(Game.home_score))
    elif sort_by == "away_score":
        if sort_desc:
            query = query.order_by(desc(Game.away_score))
        else:
            query = query.order_by(asc(Game.away_score))
    # Add other sorting options as needed
    
    if limit:
        return query.offset(skip).limit(limit).all()
    return query.offset(skip).all()


def get_game_by_id(db: Session, game_id: int) -> Optional[Game]:
    """
    Get a game by internal ID.
    """
    return db.query(Game).filter(Game.id == game_id).first()


def get_game_by_game_id(db: Session, game_id: str) -> Optional[Game]:
    """
    Get a game by external game_id (e.g., NHL API ID).
    """
    return db.query(Game).options(
        joinedload(Game.home_team),
        joinedload(Game.away_team)
    ).filter(Game.game_id == game_id).first()


def create_game(db: Session, game: GameCreate) -> Game:
    """
    Create a new game.
    """
    # Get team IDs
    home_team = db.query(Team).filter(Team.team_id == game.home_team_id).first()
    away_team = db.query(Team).filter(Team.team_id == game.away_team_id).first()
    
    if not home_team or not away_team:
        raise ValueError("Home team or away team not found")
    
    db_game = Game(
        game_id=game.game_id,
        date=game.date,
        home_team_id=home_team.id,
        away_team_id=away_team.id,
        season=game.season,
        status=game.status,
        period=game.period,
        time_remaining=game.time_remaining,
        home_score=game.home_score,
        away_score=game.away_score
    )
    db.add(db_game)
    db.commit()
    db.refresh(db_game)
    return db_game


def update_game(db: Session, game_id: str, game_update: GameUpdate) -> Optional[Game]:
    """
    Update a game by game_id.
    """
    db_game = get_game_by_game_id(db, game_id)
    if not db_game:
        return None
    
    game_data = game_update.dict(exclude_unset=True)
    
    # Handle team IDs if provided
    if "home_team_id" in game_data:
        home_team_id = game_data.pop("home_team_id")
        if home_team_id:
            home_team = db.query(Team).filter(Team.team_id == home_team_id).first()
            if home_team:
                game_data["home_team_id"] = home_team.id
    
    if "away_team_id" in game_data:
        away_team_id = game_data.pop("away_team_id")
        if away_team_id:
            away_team = db.query(Team).filter(Team.team_id == away_team_id).first()
            if away_team:
                game_data["away_team_id"] = away_team.id
    
    for key, value in game_data.items():
        setattr(db_game, key, value)
    
    db.commit()
    db.refresh(db_game)
    return db_game


def delete_game(db: Session, game_id: str) -> bool:
    """
    Delete a game by game_id.
    """
    db_game = get_game_by_game_id(db, game_id)
    if not db_game:
        return False
    
    # You might want to add cascade delete for related events
    db.delete(db_game)
    db.commit()
    return True


def get_game_stats(db: Session, game_id: str) -> Dict[str, Any]:
    """
    Get detailed statistics for a game.
    """
    db_game = get_game_by_game_id(db, game_id)
    if not db_game:
        return {"error": "Game not found"}
    
    # Get team stats for this game
    home_team_stats = db.query(TeamGameStats).filter(
        and_(
            TeamGameStats.game_id == db_game.id,
            TeamGameStats.team_id == db_game.home_team_id
        )
    ).first()
    
    away_team_stats = db.query(TeamGameStats).filter(
        and_(
            TeamGameStats.game_id == db_game.id,
            TeamGameStats.team_id == db_game.away_team_id
        )
    ).first()
    
    # Basic game info
    game_info = {
        "id": db_game.id,
        "game_id": db_game.game_id,
        "date": db_game.date,
        "season": db_game.season,
        "status": db_game.status,
        "period": db_game.period,
        "time_remaining": db_game.time_remaining,
        "home_score": db_game.home_score,
        "away_score": db_game.away_score,
        "home_team": {
            "id": db_game.home_team.id,
            "team_id": db_game.home_team.team_id,
            "name": db_game.home_team.name,
            "abbreviation": db_game.home_team.abbreviation
        },
        "away_team": {
            "id": db_game.away_team.id,
            "team_id": db_game.away_team.team_id,
            "name": db_game.away_team.name,
            "abbreviation": db_game.away_team.abbreviation
        }
    }
    
    # Add team stats if available
    if home_team_stats:
        game_info["home_team_stats"] = {
            "shots": home_team_stats.shots,
            "hits": home_team_stats.hits,
            "blocks": home_team_stats.blocks,
            "pim": home_team_stats.pim,
            "faceoff_wins": home_team_stats.faceoff_wins,
            "faceoff_losses": home_team_stats.faceoff_losses,
            "xg": home_team_stats.xg,
            "xg_against": home_team_stats.xg_against,
            "corsi_for": home_team_stats.corsi_for,
            "corsi_against": home_team_stats.corsi_against,
            # Add more stats as needed
        }
    else:
        game_info["home_team_stats"] = None
    
    if away_team_stats:
        game_info["away_team_stats"] = {
            "shots": away_team_stats.shots,
            "hits": away_team_stats.hits,
            "blocks": away_team_stats.blocks,
            "pim": away_team_stats.pim,
            "faceoff_wins": away_team_stats.faceoff_wins,
            "faceoff_losses": away_team_stats.faceoff_losses,
            "xg": away_team_stats.xg,
            "xg_against": away_team_stats.xg_against,
            "corsi_for": away_team_stats.corsi_for,
            "corsi_against": away_team_stats.corsi_against,
            # Add more stats as needed
        }
    else:
        game_info["away_team_stats"] = None
    
    return game_info