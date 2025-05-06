import logging
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_, desc, asc

from app.models.base import Team, Player, Game, GameEvent
from app.models.analytics import ShotEvent, ZoneEntry, Pass, PuckRecovery

logger = logging.getLogger(__name__)


class MetricsService:
    """
    Service for calculating various performance metrics.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_ecr(self, player_id: Optional[int] = None, team_id: Optional[int] = None, game_id: Optional[int] = None) -> float:
        """
        Calculate Entry Conversion Rate (ECR).
        
        Args:
            player_id: Filter by player
            team_id: Filter by team
            game_id: Filter by game
            
        Returns:
            ECR value (0-1)
        """
        # Base query for zone entries
        query = self.db.query(ZoneEntry)
        
        # Apply filters
        if player_id:
            query = query.filter(ZoneEntry.player_id == player_id)
        
        if team_id:
            query = query.join(ZoneEntry.event).filter(ZoneEntry.event.has(team_id=team_id))
        
        if game_id:
            query = query.join(ZoneEntry.event).filter(ZoneEntry.event.has(game_id=game_id))
        
        # Get controlled entries only
        entries = query.filter(ZoneEntry.controlled == True).all()
        
        # Calculate ECR
        total_controlled_entries = len(entries)
        successful_entries = sum(1 for entry in entries if entry.lead_to_shot)
        
        if total_controlled_entries == 0:
            return 0.0
        
        return successful_entries / total_controlled_entries
    
    def calculate_pri(self, player_id: Optional[int] = None, team_id: Optional[int] = None, game_id: Optional[int] = None) -> float:
        """
        Calculate Puck Recovery Impact (PRI).
        
        Args:
            player_id: Filter by player
            team_id: Filter by team
            game_id: Filter by game
            
        Returns:
            PRI value
        """
        # Base query for puck recoveries
        query = self.db.query(PuckRecovery)
        
        # Apply filters
        if player_id:
            query = query.filter(PuckRecovery.player_id == player_id)
        
        if team_id:
            query = query.join(PuckRecovery.event).filter(PuckRecovery.event.has(team_id=team_id))
        
        if game_id:
            query = query.join(PuckRecovery.event).filter(PuckRecovery.event.has(game_id=game_id))
        
        # Get recoveries
        recoveries = query.all()
        
        # Calculate PRI (simplified version)
        pri_score = 0.0
        
        for recovery in recoveries:
            # Weight based on zone
            zone_weight = 1.0
            if recovery.zone == "OZ":
                zone_weight = 2.0  # Offensive zone recoveries are more valuable
            elif recovery.zone == "DZ":
                zone_weight = 0.5  # Defensive zone recoveries less valuable
            
            # Weight based on outcome
            outcome_weight = 1.0
            if recovery.lead_to_possession:
                outcome_weight = 1.5  # Recoveries leading to possession are more valuable
            
            # Recovery type weight
            type_weight = 1.0
            if recovery.recovery_type == "forecheck":
                type_weight = 1.5  # Forecheck recoveries are more valuable
            elif recovery.recovery_type == "takeaway":
                type_weight = 2.0  # Takeaways are most valuable
            
            # Add to total score
            pri_score += zone_weight * outcome_weight * type_weight
        
        return pri_score
    
    def calculate_shot_metrics(self, player_id: Optional[int] = None, team_id: Optional[int] = None, game_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Calculate shot-based metrics.
        
        Args:
            player_id: Filter by player
            team_id: Filter by team
            game_id: Filter by game
            
        Returns:
            Dictionary of shot metrics
        """
        # Base query for shots
        query = self.db.query(ShotEvent)
        
        # Apply filters
        if player_id:
            query = query.filter(ShotEvent.shooter_id == player_id)
        
        if team_id:
            query = query.join(ShotEvent.event).filter(ShotEvent.event.has(team_id=team_id))
        
        if game_id:
            query = query.join(ShotEvent.event).filter(ShotEvent.event.has(game_id=game_id))
        
        # Get shots
        shots = query.all()
        
        # Calculate metrics
        total_shots = len(shots)
        if total_shots == 0:
            return {
                "total_shots": 0,
                "goals": 0,
                "shooting_percentage": 0.0,
                "total_xg": 0.0,
                "avg_xg": 0.0,
                "xg_performance": 0.0
            }
        
        goals = sum(1 for shot in shots if shot.goal)
        total_xg = sum(shot.xg or 0 for shot in shots)
        avg_xg = total_xg / total_shots
        shooting_percentage = (goals / total_shots) * 100
        xg_performance = goals - total_xg  # Goals above expected
        
        return {
            "total_shots": total_shots,
            "goals": goals,
            "shooting_percentage": shooting_percentage,
            "total_xg": total_xg,
            "avg_xg": avg_xg,
            "xg_performance": xg_performance
        }
    
    def calculate_player_metrics(self, player_id: str) -> Dict[str, Any]:
        """
        Calculate all metrics for a player.
        
        Args:
            player_id: Player ID
            
        Returns:
            Dictionary of player metrics
        """
        # Get player
        player = self.db.query(Player).filter(Player.player_id == player_id).first()
        if not player:
            return {"error": "Player not found"}
        
        # Calculate metrics
        ecr = self.calculate_ecr(player_id=player.id)
        pri = self.calculate_pri(player_id=player.id)
        shot_metrics = self.calculate_shot_metrics(player_id=player.id)
        
        # Get basic player stats
        total_events = self.db.query(GameEvent).filter(GameEvent.player_id == player.id).count()
        
        # Get team
        team_info = None
        if player.team_id:
            team = self.db.query(Team).filter(Team.id == player.team_id).first()
            if team:
                team_info = {
                    "id": team.id,
                    "team_id": team.team_id,
                    "name": team.name,
                    "abbreviation": team.abbreviation
                }
        
        # Calculate ICE+ (simplified version)
        # In reality, would use weighted components based on position
        ice_plus = 0.0
        
        # Add components with position-specific weighting
        if shot_metrics["total_shots"] > 0:
            ice_plus += shot_metrics["xg_performance"] * 2.0  # Weight shooting performance
        
        ice_plus += ecr * 1.5  # Weight zone entries
        ice_plus += pri * 1.2  # Weight puck recoveries
        
        return {
            "player_id": player_id,
            "name": player.name,
            "position": player.position,
            "team": team_info,
            "ecr": ecr,
            "pri": pri,
            "shot_metrics": shot_metrics,
            "total_events": total_events,
            "ice_plus": ice_plus  # Simplified ICE+ score
        }
    
    def calculate_team_metrics(self, team_id: str) -> Dict[str, Any]:
        """
        Calculate all metrics for a team.
        
        Args:
            team_id: Team ID
            
        Returns:
            Dictionary of team metrics
        """
        # Get team
        team = self.db.query(Team).filter(Team.team_id == team_id).first()
        if not team:
            return {"error": "Team not found"}
        
        # Calculate metrics
        ecr = self.calculate_ecr(team_id=team.id)
        pri = self.calculate_pri(team_id=team.id)
        shot_metrics = self.calculate_shot_metrics(team_id=team.id)
        
        # Get players on team
        players = self.db.query(Player).filter(Player.team_id == team.id).all()
        
        # Get basic team stats
        total_events = self.db.query(GameEvent).filter(GameEvent.team_id == team.id).count()
        
        return {
            "team_id": team_id,
            "name": team.name,
            "abbreviation": team.abbreviation,
            "ecr": ecr,
            "pri": pri,
            "shot_metrics": shot_metrics,
            "total_events": total_events,
            "player_count": len(players)
        }