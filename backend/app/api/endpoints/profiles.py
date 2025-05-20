from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from app.db.session import get_db
from app.models.base import GameEvent, Player, Team
from app.models.analytics import PlayerProfile, TeamProfile, Game, ShotEvent, ZoneEntry
from app.services.metrics_service import MetricsService

router = APIRouter()

@router.get("/player/{player_id}")
def get_player_profile(
    player_id: int,
    season: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get comprehensive player profile
    """
    # Get the player
    player = db.query(Player).filter(Player.player_id == str(player_id)).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    # Check if we have a profile for this player
    profile = db.query(PlayerProfile).filter(
        PlayerProfile.player_id == player.id,
        PlayerProfile.season == season if season else True
    ).first()
    
    # If no profile exists, generate one
    if not profile:
        profile_data = generate_player_profile(db, player, season)
    else:
        # Use existing profile
        profile_data = {
            "id": profile.id,
            "player_id": player_id,
            "name": player.name,
            "season": profile.season,
            "primary_role": profile.primary_role,
            "secondary_role": profile.secondary_role,
            "offensive_behavior": profile.offensive_behavior,
            "defensive_behavior": profile.defensive_behavior,
            "transition_behavior": profile.transition_behavior,
            "current_team_fit": profile.current_team_fit,
            "optimal_system_type": profile.optimal_system_type,
            "system_fit_scores": profile.system_fit_scores,
            "season_ice_plus": profile.season_ice_plus,
            "consistency_metrics": profile.consistency_metrics
        }
    
    return profile_data

@router.get("/team/{team_id}")
def get_team_profile(
    team_id: int,
    season: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get comprehensive team profile
    """
    # Get the team
    team = db.query(Team).filter(Team.team_id == str(team_id)).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Check if we have a profile for this team
    profile = db.query(TeamProfile).filter(
        TeamProfile.team_id == team.id,
        TeamProfile.season == season if season else True
    ).first()
    
    # If no profile exists, generate one
    if not profile:
        profile_data = generate_team_profile(db, team, season)
    else:
        # Use existing profile
        profile_data = {
            "id": profile.id,
            "team_id": team_id,
            "name": team.name,
            "season": profile.season,
            "offensive_style": profile.offensive_style,
            "defensive_style": profile.defensive_style,
            "special_teams": profile.special_teams,
            "team_fingerprint": profile.team_fingerprint,
            "similar_teams": profile.similar_teams
        }
    
    return profile_data

def generate_player_profile(db, player, season=None):
    """Generate a player profile based on available data."""
    metrics_service = MetricsService(db)
    
    # Query to filter data by season if needed
    season_filter = lambda q: q.join(Game, GameEvent.game_id == Game.game_id).filter(Game.season == season) if season else q
    
    # Get basic stats
    shots = db.query(ShotEvent).join(GameEvent).filter(ShotEvent.shooter_id == player.id)
    shots = season_filter(shots).all()
    
    entries = db.query(ZoneEntry).join(GameEvent).filter(ZoneEntry.player_id == player.id)
    entries = season_filter(entries).all()
    
    # Calculate metrics
    ecr = metrics_service.calculate_ecr(player_id=player.id)
    pri = metrics_service.calculate_pri(player_id=player.id)
    pdi = metrics_service.calculate_pdi(player_id=player.id)
    
    # Determine role
    position = player.position
    
    if position in ["C", "Center"]:
        primary_role = "Center"
    elif position in ["LW", "RW", "Left Wing", "Right Wing"]:
        primary_role = "Winger"
    elif position in ["D", "Defense"]:
        primary_role = "Defenseman"
    elif position in ["G", "Goalie"]:
        primary_role = "Goalie"
    else:
        primary_role = "Forward"
    
    # Secondary role is based on play style
    # High PRI indicates a defensive player
    # High shot count indicates an offensive player
    if pri > 10:
        secondary_role = "Defensive Specialist"
    elif len(shots) > 50:
        secondary_role = "Offensive Producer"
    else:
        secondary_role = "Two-Way Player"
    
    # Create profile data
    profile_data = {
        "player_id": int(player.player_id),
        "name": player.name,
        "season": season,
        "primary_role": primary_role,
        "secondary_role": secondary_role,
        "offensive_behavior": {
            "shot_count": len(shots),
            "goals": sum(1 for s in shots if s.goal),
            "shooting_percentage": sum(1 for s in shots if s.goal) / len(shots) * 100 if len(shots) > 0 else 0,
            "shot_types": {},  # Would be populated with actual shot type distribution
            "pass_tendencies": {}  # Would be populated with pass data
        },
        "defensive_behavior": {
            "pdi": pdi,
            "zone_bias": "Offensive" if ecr > 0.5 else "Defensive",
            "recovery_count": 0  # Would be populated with recovery count
        },
        "transition_behavior": {
            "ecr": ecr,
            "controlled_entries": sum(1 for e in entries if e.controlled),
            "dump_ins": sum(1 for e in entries if not e.controlled),
            "entry_types": {}  # Would be populated with entry type distribution
        },
        "current_team_fit": 0.75,  # Placeholder value
        "optimal_system_type": "Possession-based",  # Placeholder value
        "system_fit_scores": {},  # Would contain fit scores for different teams
        "season_ice_plus": ecr * 2 + pri * 1.5 + pdi,  # Simple calculation
        "consistency_metrics": {
            "variance": 0.2,  # Placeholder value
            "trend": "Stable"  # Placeholder value
        }
    }
    
    return profile_data

def generate_team_profile(db, team, season=None):
    """Generate a team profile based on available data."""
    metrics_service = MetricsService(db)
    
    # Get team metrics
    team_metrics = metrics_service.calculate_team_metrics(int(team.team_id))
    
    # Create profile data
    profile_data = {
        "team_id": int(team.team_id),
        "name": team.name,
        "season": season,
        "offensive_style": {
            "tempo": "Fast",  # Placeholder - would be derived from actual data
            "shot_selection": "High Volume",  # Placeholder
            "entry_style": "Controlled" if team_metrics.get("ecr", 0) > 0.5 else "Dump and Chase"
        },
        "defensive_style": {
            "forecheck": "Aggressive",  # Placeholder
            "neutral_zone": "Trap",  # Placeholder
            "defensive_zone": "Zone" if team_metrics.get("pdi", 0) > 20 else "Man-to-Man"
        },
        "special_teams": {
            "pp_formations": ["1-3-1"],  # Placeholder
            "pk_formations": ["Diamond"]  # Placeholder
        },
        "team_fingerprint": {
            "ecr": team_metrics.get("ecr", 0),
            "pri": team_metrics.get("pri", 0),
            "goals_per_game": 3.2,  # Placeholder
            "shots_per_game": 31.5  # Placeholder
        },
        "similar_teams": [
            {"team_id": 1, "name": "Toronto Maple Leafs", "similarity": 0.92},
            {"team_id": 7, "name": "Boston Bruins", "similarity": 0.87},
            {"team_id": 12, "name": "Carolina Hurricanes", "similarity": 0.85}
        ]  # Placeholder similar teams
    }
    
    return profile_data