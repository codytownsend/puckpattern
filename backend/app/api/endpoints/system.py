from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from app.db.session import get_db
from app.models.base import Team
from app.models.analytics import Game, TeamGameStats, GameEvent, ShotEvent, ZoneEntry
from app.services.metrics_service import MetricsService

router = APIRouter()

@router.get("/team/{team_id}")
def get_team_system(
    team_id: int,
    season: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get team system detection data
    """
    # Get the team
    team = db.query(Team).filter(Team.team_id == str(team_id)).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Query team game stats
    query = db.query(TeamGameStats).filter(TeamGameStats.team_id == team.id)
    
    if season:
        query = query.join(Game, TeamGameStats.game_id == Game.id).filter(Game.season == season)
    
    team_stats = query.all()
    
    # Calculate system metrics
    system_data = analyze_team_system(db, team_stats, team, season)
    
    return system_data

@router.get("/compare/{team1_id}/{team2_id}")
def compare_team_systems(
    team1_id: int,
    team2_id: int,
    season: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Compare systems between two teams
    """
    # Get team 1 data
    team1 = db.query(Team).filter(Team.team_id == str(team1_id)).first()
    if not team1:
        raise HTTPException(status_code=404, detail=f"Team {team1_id} not found")
    
    # Get team 2 data
    team2 = db.query(Team).filter(Team.team_id == str(team2_id)).first()
    if not team2:
        raise HTTPException(status_code=404, detail=f"Team {team2_id} not found")
    
    # Get system data for both teams
    team1_system = get_team_system(team1_id, season, db)
    team2_system = get_team_system(team2_id, season, db)
    
    # Calculate similarity between systems
    similarity = calculate_system_similarity(team1_system, team2_system)
    
    # Identify key differences
    differences = {
        "forecheck": {
            "difference": team1_system["forecheck"]["style"] != team2_system["forecheck"]["style"],
            "team1": team1_system["forecheck"]["style"],
            "team2": team2_system["forecheck"]["style"],
        },
        "defensive_structure": {
            "difference": team1_system["defensive_structure"]["primary"] != team2_system["defensive_structure"]["primary"],
            "team1": team1_system["defensive_structure"]["primary"],
            "team2": team2_system["defensive_structure"]["primary"],
        },
        "transition": {
            "difference": team1_system["transition"]["entry_preference"] != team2_system["transition"]["entry_preference"],
            "team1": team1_system["transition"]["entry_preference"],
            "team2": team2_system["transition"]["entry_preference"],
        }
    }
    
    return {
        "teams": [
            {"team_id": team1_id, "name": team1.name, "system": team1_system},
            {"team_id": team2_id, "name": team2.name, "system": team2_system}
        ],
        "similarity_score": similarity,
        "key_differences": differences
    }

@router.get("/league_comparison/{team_id}")
def get_league_system_comparison(
    team_id: int,
    season: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Compare team system to league averages and other teams
    """
    # Get the team
    team = db.query(Team).filter(Team.team_id == str(team_id)).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Get team system
    team_system = get_team_system(team_id, season, db)
    
    # Get league averages (would require analyzing all teams)
    # Placeholder implementation
    league_averages = {
        "forecheck_aggression": 0.5,
        "defensive_structure": {
            "zone": 0.5,
            "man": 0.3,
            "hybrid": 0.2
        },
        "transition_control": 0.55,
        "system_tempo": "medium"
    }
    
    # Most similar teams (would require comparing to all teams)
    # Placeholder implementation
    similar_teams = [
        {"team_id": 10, "name": "Example Team 1", "similarity": 0.92},
        {"team_id": 13, "name": "Example Team 2", "similarity": 0.87},
        {"team_id": 18, "name": "Example Team 3", "similarity": 0.85}
    ]
    
    # Calculate where team ranks in various system metrics
    # Placeholder implementation
    rankings = {
        "forecheck_aggression": {"rank": 7, "percentile": 0.78},
        "defensive_pressure": {"rank": 12, "percentile": 0.63},
        "transition_control": {"rank": 3, "percentile": 0.91},
        "system_tempo": {"rank": 5, "percentile": 0.85}
    }
    
    return {
        "team_id": team_id,
        "name": team.name,
        "season": season,
        "team_system": team_system,
        "league_averages": league_averages,
        "similar_teams": similar_teams,
        "system_rankings": rankings
    }

def analyze_team_system(db, team_stats, team, season=None):
    """Analyze team system based on available data."""
    metrics_service = MetricsService(db)
    
    # Calculate metrics
    team_id = int(team.team_id)
    ecr = metrics_service.calculate_ecr(team_id=team.id)
    pri = metrics_service.calculate_pri(team_id=team.id)
    
    # Count common forecheck styles from stats
    forecheck_styles = {}
    for stat in team_stats:
        if stat.forecheck_style:
            forecheck_styles[stat.forecheck_style] = forecheck_styles.get(stat.forecheck_style, 0) + 1
    
    # Find most common forecheck style
    forecheck_style = max(forecheck_styles.items(), key=lambda x: x[1])[0] if forecheck_styles else "STANDARD"
    
    # Count common defensive structures from stats
    defensive_structures = {}
    for stat in team_stats:
        if stat.defensive_structure:
            defensive_structures[stat.defensive_structure] = defensive_structures.get(stat.defensive_structure, 0) + 1
    
    # Find most common defensive structure
    defensive_structure = max(defensive_structures.items(), key=lambda x: x[1])[0] if defensive_structures else "ZONE"
    
    # Analyze zone entries to determine transition style
    entries_query = db.query(ZoneEntry).join(GameEvent).filter(GameEvent.team_id == team.id)
    
    if season:
        entries_query = entries_query.join(Game, GameEvent.game_id == Game.game_id).filter(Game.season == season)
    
    entries = entries_query.all()
    
    # Calculate controlled vs. dump-in ratio
    controlled_entries = sum(1 for e in entries if e.controlled)
    total_entries = len(entries)
    controlled_ratio = controlled_entries / total_entries if total_entries > 0 else 0
    
    # Determine transition style based on controlled entry ratio
    if controlled_ratio > 0.7:
        transition_style = "Possession-focused"
        entry_preference = "Controlled"
    elif controlled_ratio < 0.4:
        transition_style = "Dump and chase"
        entry_preference = "Uncontrolled"
    else:
        transition_style = "Balanced"
        entry_preference = "Mixed"
    
    # Return complete system analysis
    return {
        "team_id": team_id,
        "name": team.name,
        "forecheck": {
            "style": forecheck_style,
            "aggression": "High" if forecheck_style == "AGGRESSIVE" else "Medium" if forecheck_style == "STANDARD" else "Low",
            "pressure_points": ["Defensive zone corners", "Neutral zone center"] if forecheck_style == "AGGRESSIVE" else ["Neutral zone"]
        },
        "defensive_structure": {
            "primary": defensive_structure,
            "collapse_tendency": "High" if defensive_structure == "COLLAPSE" else "Medium",
            "pressure_points": ["Slot", "Net front"] if defensive_structure == "COLLAPSE" else ["Point", "Wings"]
        },
        "transition": {
            "style": transition_style,
            "entry_preference": entry_preference,
            "controlled_entry_ratio": controlled_ratio,
            "rush_tendency": "High" if pri > 15 else "Medium" if pri > 8 else "Low"
        },
        "offensive_zone": {
            "cycle_preference": "High" if pri > 10 else "Medium",
            "low_to_high_frequency": "Medium",
            "net_front_presence": "Strong" if pri > 12 else "Medium"
        },
        "overall_tempo": "Fast-paced" if ecr > 0.6 and controlled_ratio > 0.6 else "Methodical" if ecr < 0.4 else "Balanced",
        "system_metrics": {
            "ecr": ecr,
            "pri": pri
        }
    }

def calculate_system_similarity(system1, system2):
    """Calculate similarity between two team systems."""
    similarity_score = 0.0
    total_weight = 0.0
    
    # Compare forecheck styles (weight: 0.3)
    if system1["forecheck"]["style"] == system2["forecheck"]["style"]:
        similarity_score += 0.3
    elif system1["forecheck"]["aggression"] == system2["forecheck"]["aggression"]:
        similarity_score += 0.15
    total_weight += 0.3
    
    # Compare defensive structures (weight: 0.3)
    if system1["defensive_structure"]["primary"] == system2["defensive_structure"]["primary"]:
        similarity_score += 0.3
    elif system1["defensive_structure"]["collapse_tendency"] == system2["defensive_structure"]["collapse_tendency"]:
        similarity_score += 0.15
    total_weight += 0.3
    
    # Compare transition styles (weight: 0.25)
    if system1["transition"]["style"] == system2["transition"]["style"]:
        similarity_score += 0.25
    elif system1["transition"]["entry_preference"] == system2["transition"]["entry_preference"]:
        similarity_score += 0.125
    total_weight += 0.25
    
    # Compare overall tempo (weight: 0.15)
    if system1["overall_tempo"] == system2["overall_tempo"]:
        similarity_score += 0.15
    total_weight += 0.15
    
    # Normalize score
    return similarity_score / total_weight if total_weight > 0 else 0.0