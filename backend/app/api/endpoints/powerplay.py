from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from app.db.session import get_db
from app.models.base import Team
from app.models.analytics import Game, PowerPlay, GameEvent, ShotEvent

router = APIRouter()

@router.get("/team/{team_id}")
def get_team_powerplay_stats(
    team_id: int,
    season: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get comprehensive power play stats for a team
    """
    # Get the team
    team = db.query(Team).filter(Team.team_id == str(team_id)).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Query power plays
    query = db.query(PowerPlay).filter(PowerPlay.team_id == team.id)
    
    if season:
        query = query.join(Game, PowerPlay.game_id == Game.id).filter(Game.season == season)
    
    power_plays = query.all()
    
    # Calculate stats
    pp_stats = calculate_pp_stats(db, power_plays, team.id)
    
    # Query PK (when team is not on PP)
    pk_query = db.query(PowerPlay).join(Game)
    
    # For PK, we need to find power plays where this team's opponent is on PP
    # This requires matching games where this team appears
    pk_query = pk_query.filter(
        ((Game.home_team_id == team.id) & (PowerPlay.team_id != team.id)) |
        ((Game.away_team_id == team.id) & (PowerPlay.team_id != team.id))
    )
    
    if season:
        pk_query = pk_query.filter(Game.season == season)
    
    penalty_kills = pk_query.all()
    
    # Calculate PK stats
    pk_stats = calculate_pk_stats(db, penalty_kills, team.id)
    
    return {
        "team_id": team_id,
        "name": team.name,
        "season": season,
        "power_play": pp_stats,
        "penalty_kill": pk_stats
    }

@router.get("/compare/{team1_id}/{team2_id}")
def compare_powerplays(
    team1_id: int,
    team2_id: int,
    season: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Compare power play stats between two teams
    """
    # Get team 1 stats
    team1 = db.query(Team).filter(Team.team_id == str(team1_id)).first()
    if not team1:
        raise HTTPException(status_code=404, detail=f"Team {team1_id} not found")
    
    # Get team 2 stats
    team2 = db.query(Team).filter(Team.team_id == str(team2_id)).first()
    if not team2:
        raise HTTPException(status_code=404, detail=f"Team {team2_id} not found")
    
    # Get stats for both teams
    team1_stats = get_team_powerplay_stats(team1_id, season, db)
    team2_stats = get_team_powerplay_stats(team2_id, season, db)
    
    # Format comparison
    comparison = {
        "teams": [
            {
                "team_id": team1_id,
                "name": team1.name,
                "stats": team1_stats
            },
            {
                "team_id": team2_id,
                "name": team2.name,
                "stats": team2_stats
            }
        ],
        "power_play_comparison": {
            "success_rate_diff": team1_stats["power_play"]["success_rate"] - team2_stats["power_play"]["success_rate"],
            "shots_per_pp_diff": team1_stats["power_play"]["shots_per_pp"] - team2_stats["power_play"]["shots_per_pp"],
            "pp_time_diff": team1_stats["power_play"]["avg_pp_time"] - team2_stats["power_play"]["avg_pp_time"]
        },
        "penalty_kill_comparison": {
            "success_rate_diff": team1_stats["penalty_kill"]["success_rate"] - team2_stats["penalty_kill"]["success_rate"],
            "shots_allowed_diff": team1_stats["penalty_kill"]["shots_allowed_per_pk"] - team2_stats["penalty_kill"]["shots_allowed_per_pk"],
            "pk_time_diff": team1_stats["penalty_kill"]["avg_pk_time"] - team2_stats["penalty_kill"]["avg_pk_time"]
        }
    }
    
    return comparison

@router.get("/formations/{team_id}")
def get_powerplay_formations(
    team_id: int,
    season: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get power play formations for a team
    """
    # Get the team
    team = db.query(Team).filter(Team.team_id == str(team_id)).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Analyze power play formations using shot and pass locations
    # This would require analysis of spatial data during power plays
    
    # Simplified placeholder implementation
    formations = {
        "team_id": team_id,
        "name": team.name,
        "season": season,
        "primary_formation": "1-3-1",
        "secondary_formation": "Umbrella",
        "formation_usage": {
            "1-3-1": 0.65,
            "Umbrella": 0.25,
            "Overload": 0.10
        },
        "success_rates": {
            "1-3-1": 0.22,
            "Umbrella": 0.18,
            "Overload": 0.15
        },
        "shot_maps": {
            "1-3-1": {
                "total_shots": 45,
                "goals": 10,
                "top_shooters": [
                    {"player_id": 8478402, "name": "Player Name", "shots": 15, "goals": 4}
                ]
            }
        }
    }
    
    return formations

def calculate_pp_stats(db, power_plays, team_id):
    """Calculate power play statistics from power play records."""
    if not power_plays:
        return {
            "opportunities": 0,
            "goals": 0,
            "success_rate": 0,
            "total_pp_time": 0,
            "avg_pp_time": 0,
            "shots": 0,
            "shots_per_pp": 0,
            "formations": {}
        }
    
    # Count opportunities
    opportunities = len(power_plays)
    
    # Count goals
    goals = sum(1 for pp in power_plays if pp.successful)
    
    # Calculate success rate
    success_rate = goals / opportunities if opportunities > 0 else 0
    
    # Calculate PP time stats
    total_pp_time = sum(pp.duration for pp in power_plays)
    avg_pp_time = total_pp_time / opportunities if opportunities > 0 else 0
    
    # Count shots
    total_shots = sum(pp.pp_shots or 0 for pp in power_plays)
    shots_per_pp = total_shots / opportunities if opportunities > 0 else 0
    
    # Count formations
    formation_counts = {}
    for pp in power_plays:
        if pp.pp_formation:
            formation_counts[pp.pp_formation] = formation_counts.get(pp.pp_formation, 0) + 1
    
    # Convert to percentages
    formations = {
        formation: count / opportunities
        for formation, count in formation_counts.items()
    }
    
    return {
        "opportunities": opportunities,
        "goals": goals,
        "success_rate": success_rate,
        "total_pp_time": total_pp_time,
        "avg_pp_time": avg_pp_time,
        "shots": total_shots,
        "shots_per_pp": shots_per_pp,
        "formations": formations
    }

def calculate_pk_stats(db, penalty_kills, team_id):
    """Calculate penalty kill statistics from power play records."""
    if not penalty_kills:
        return {
            "times_shorthanded": 0,
            "goals_allowed": 0,
            "success_rate": 0,
            "total_pk_time": 0,
            "avg_pk_time": 0,
            "shots_allowed": 0,
            "shots_allowed_per_pk": 0,
            "formations": {}
        }
    
    # Count times shorthanded
    times_shorthanded = len(penalty_kills)
    
    # Count goals allowed
    goals_allowed = sum(1 for pk in penalty_kills if pk.successful)
    
    # Calculate success rate (kills/times shorthanded)
    success_rate = (times_shorthanded - goals_allowed) / times_shorthanded if times_shorthanded > 0 else 0
    
    # Calculate PK time stats
    total_pk_time = sum(pk.duration for pk in penalty_kills)
    avg_pk_time = total_pk_time / times_shorthanded if times_shorthanded > 0 else 0
    
    # Count shots allowed
    total_shots_allowed = sum(pk.pp_shots or 0 for pk in penalty_kills)
    shots_allowed_per_pk = total_shots_allowed / times_shorthanded if times_shorthanded > 0 else 0
    
    return {
        "times_shorthanded": times_shorthanded,
        "goals_allowed": goals_allowed,
        "success_rate": success_rate,
        "total_pk_time": total_pk_time,
        "avg_pk_time": avg_pk_time,
        "shots_allowed": total_shots_allowed,
        "shots_allowed_per_pk": shots_allowed_per_pk,
        "formations": {
            "Box": 0.6,  # Placeholder values
            "Diamond": 0.3,
            "Triangle+1": 0.1
        }
    }