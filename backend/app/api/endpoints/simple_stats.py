"""
Simple API endpoints for the new database structure
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db.session import get_db
from app.models import (
    Team, Player, Season, TeamRoster, 
    PlayerSeasonStats, TeamSeasonStats
)

router = APIRouter()

# ============================================================================
# BASIC DATA ENDPOINTS
# ============================================================================

@router.get("/seasons")
def get_seasons(db: Session = Depends(get_db)):
    """Get all available seasons"""
    seasons = db.query(Season).order_by(desc(Season.season_id)).all()
    return [
        {
            "season_id": s.season_id,
            "start_date": s.start_date,
            "end_date": s.end_date,
            "is_current": s.is_current
        }
        for s in seasons
    ]

@router.get("/teams")
def get_teams(db: Session = Depends(get_db)):
    """Get all teams"""
    teams = db.query(Team).order_by(Team.name).all()
    return [
        {
            "team_id": t.team_id,
            "name": t.name,
            "abbreviation": t.abbreviation,
            "city": t.city,
            "conference": t.conference,
            "division": t.division
        }
        for t in teams
    ]

@router.get("/players")
def get_players(
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get players with optional search"""
    query = db.query(Player)
    
    if search:
        query = query.filter(Player.name.ilike(f"%{search}%"))
    
    players = query.order_by(Player.name).offset(offset).limit(limit).all()
    
    return [
        {
            "player_id": p.player_id,
            "name": p.name,
            "position": p.position,
            "birth_date": p.birth_date,
            "height_inches": p.height_inches,
            "weight_pounds": p.weight_pounds
        }
        for p in players
    ]

# ============================================================================
# TEAM STATS ENDPOINTS  
# ============================================================================

@router.get("/teams/{team_id}/stats")
def get_team_stats(
    team_id: str,
    season_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get team statistics"""
    # Verify team exists
    team = db.query(Team).filter(Team.team_id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Get stats query
    query = db.query(TeamSeasonStats).filter(TeamSeasonStats.team_id == team_id)
    
    if season_id:
        query = query.filter(TeamSeasonStats.season_id == season_id)
    
    stats = query.order_by(desc(TeamSeasonStats.season_id)).all()
    
    return {
        "team": {
            "team_id": team.team_id,
            "name": team.name,
            "abbreviation": team.abbreviation
        },
        "seasons": [
            {
                "season_id": s.season_id,
                "games_played": s.games_played,
                "wins": s.wins,
                "losses": s.losses,
                "overtime_losses": s.overtime_losses,
                "points": s.points,
                "goals_for": s.goals_for,
                "goals_against": s.goals_against,
                "goals_per_game": s.goals_per_game,
                "goals_against_per_game": s.goals_against_per_game,
                "power_play_percentage": s.power_play_percentage,
                "penalty_kill_percentage": s.penalty_kill_percentage
            }
            for s in stats
        ]
    }

@router.get("/teams/{team_id}/roster")
def get_team_roster(
    team_id: str,
    season_id: str,
    db: Session = Depends(get_db)
):
    """Get team roster for a specific season"""
    # Verify team exists
    team = db.query(Team).filter(Team.team_id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Get roster with player info
    roster_query = db.query(TeamRoster, Player).join(
        Player, TeamRoster.player_id == Player.player_id
    ).filter(
        TeamRoster.team_id == team_id,
        TeamRoster.season_id == season_id
    ).order_by(Player.name)
    
    roster = roster_query.all()
    
    return {
        "team": {
            "team_id": team.team_id,
            "name": team.name,
            "abbreviation": team.abbreviation
        },
        "season_id": season_id,
        "roster": [
            {
                "player_id": player.player_id,
                "name": player.name,
                "position": roster_entry.position,
                "jersey_number": roster_entry.jersey_number,
                "birth_date": player.birth_date,
                "height_inches": player.height_inches,
                "weight_pounds": player.weight_pounds
            }
            for roster_entry, player in roster
        ]
    }

# ============================================================================
# PLAYER STATS ENDPOINTS
# ============================================================================

@router.get("/players/{player_id}/stats")
def get_player_stats(
    player_id: str,
    season_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get player statistics"""
    # Verify player exists
    player = db.query(Player).filter(Player.player_id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    # Get stats query with team info
    query = db.query(PlayerSeasonStats, Team).join(
        Team, PlayerSeasonStats.team_id == Team.team_id
    ).filter(PlayerSeasonStats.player_id == player_id)
    
    if season_id:
        query = query.filter(PlayerSeasonStats.season_id == season_id)
    
    stats = query.order_by(desc(PlayerSeasonStats.season_id)).all()
    
    return {
        "player": {
            "player_id": player.player_id,
            "name": player.name,
            "position": player.position,
            "birth_date": player.birth_date
        },
        "seasons": [
            {
                "season_id": stat.season_id,
                "team": {
                    "team_id": team.team_id,
                    "name": team.name,
                    "abbreviation": team.abbreviation
                },
                "games_played": stat.games_played,
                "goals": stat.goals,
                "assists": stat.assists,
                "points": stat.points,
                "shots": stat.shots,
                "shot_percentage": stat.shot_percentage,
                "power_play_goals": stat.power_play_goals,
                "power_play_points": stat.power_play_points,
                "hits": stat.hits,
                "blocks": stat.blocks,
                "penalty_minutes": stat.penalty_minutes,
                "plus_minus": stat.plus_minus,
                "avg_toi": stat.avg_toi,
                "faceoff_percentage": stat.faceoff_percentage
            }
            for stat, team in stats
        ]
    }

# ============================================================================
# SUMMARY ENDPOINTS
# ============================================================================

@router.get("/summary")
def get_database_summary(db: Session = Depends(get_db)):
    """Get summary of what's in the database"""
    return {
        "seasons": db.query(Season).count(),
        "teams": db.query(Team).count(),
        "players": db.query(Player).count(),
        "roster_entries": db.query(TeamRoster).count(),
        "player_stats_records": db.query(PlayerSeasonStats).count(),
        "team_stats_records": db.query(TeamSeasonStats).count()
    }