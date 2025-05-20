import logging
import math
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_, desc, asc

from app.models.analytics import Game
from app.models.base import Team, Player, GameEvent
from app.models.analytics import ShotEvent, ZoneEntry, Pass, PuckRecovery

logger = logging.getLogger(__name__)


class MetricsService:
    """
    Service for calculating various performance metrics.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_ecr(self, player_id=None, team_id=None, game_id=None):
        """
        Calculate Entry Conversion Rate: 
        # of controlled entries leading to a shot/chance within 10s / total controlled entries
        """
        # Query zone entries - use self.db.query instead of just query
        query = self.db.query(ZoneEntry).filter(ZoneEntry.controlled == True)
        
        # Apply filters
        if player_id:
            query = query.filter(ZoneEntry.player_id == player_id)
        if team_id:
            query = query.join(GameEvent).filter(GameEvent.team_id == team_id)
        if game_id:
            query = query.join(GameEvent).filter(GameEvent.game_id == game_id)
        
        entries = query.all()
        
        # Calculate successful entries (led to shot/chance)
        total_entries = len(entries)
        successful_entries = sum(1 for entry in entries if entry.lead_to_shot)
        
        return successful_entries / total_entries if total_entries > 0 else 0
    
    def calculate_pri(self, player_id=None, team_id=None, game_id=None):
        """Calculate Puck Recovery Impact"""
        # Query recoveries
        query = self.db.query(PuckRecovery)
        
        # Apply filters
        if player_id:
            query = query.filter(PuckRecovery.player_id == player_id)
        if team_id:
            query = query.join(GameEvent).filter(GameEvent.team_id == team_id)
        if game_id:
            query = query.join(GameEvent).filter(GameEvent.game_id == game_id)
            
        recoveries = query.all()
        
        pri_score = 0
        for recovery in recoveries:
            # Zone weights
            zone_weight = {
                "OZ": 2.0,  # Offensive zone recoveries more valuable
                "NZ": 1.0,  # Neutral zone standard value
                "DZ": 0.5   # Defensive zone less valuable for offense
            }.get(recovery.zone, 1.0)
            
            # Type weights
            type_weight = {
                "takeaway": 2.0,     # Takeaways most valuable
                "forecheck": 1.5,    # Forecheck recoveries valuable
                "loose": 1.0         # Loose puck recoveries standard value
            }.get(recovery.recovery_type, 1.0)
            
            # Outcome weight
            outcome_weight = 1.5 if recovery.lead_to_possession else 1.0
            
            pri_score += zone_weight * type_weight * outcome_weight
            
        return pri_score
    
    def calculate_xg_delta_psm(self, player_id=None, team_id=None, game_id=None):
        """
        Calculate xGΔPSM: The increase in expected goals due to passes
        """
        # Query passes that led to shots
        query = self.db.query(Pass).join(GameEvent, Pass.event_id == GameEvent.id).filter(Pass.completed == True)
        
        # Apply filters
        if player_id:
            query = query.filter(Pass.passer_id == player_id)
        if team_id:
            query = query.filter(GameEvent.team_id == team_id)
        if game_id:
            query = query.filter(GameEvent.game_id == game_id)
        
        passes = query.all()
        
        total_xg_delta = 0.0
        
        for pass_event in passes:
            # Find shot that followed this pass within 3 seconds
            pass_game_event = self.db.query(GameEvent).filter(GameEvent.id == pass_event.event_id).first()
            
            shots = self.db.query(ShotEvent).join(GameEvent, ShotEvent.event_id == GameEvent.id).filter(
                GameEvent.game_id == pass_game_event.game_id,
                GameEvent.period == pass_game_event.period,
                GameEvent.time_elapsed > pass_game_event.time_elapsed,
                GameEvent.time_elapsed <= pass_game_event.time_elapsed + 3.0
            ).all()
            
            if shots:
                # Found a shot after the pass
                shot = shots[0]
                shot_event = self.db.query(GameEvent).filter(GameEvent.id == shot.event_id).first()
                
                # Calculate hypothetical xG if shot was taken from pass location
                pass_xg = self._calculate_xg_from_location(
                    pass_game_event.x_coordinate, 
                    pass_game_event.y_coordinate
                )
                
                # Actual xG of the shot
                shot_xg = shot.xg or 0.0
                
                # Calculate delta (improvement due to pass)
                xg_delta = max(0, shot_xg - pass_xg)
                total_xg_delta += xg_delta
        
        return total_xg_delta

    def _calculate_xg_from_location(self, x_coordinate, y_coordinate):
        """
        Calculate expected goals from a specific location.
        
        Args:
            x_coordinate: X coordinate on ice
            y_coordinate: Y coordinate on ice
            
        Returns:
            Expected goals value (float)
        """
        if x_coordinate is None or y_coordinate is None:
            return 0.05  # Default value if coordinates are missing
        
        # Calculate distance to goal (assuming NHL coordinates)
        goal_x = 89.0  # X-coordinate of goal line
        goal_y = 0.0   # Y-coordinate of center of goal
        
        distance = ((x_coordinate - goal_x) ** 2 + (y_coordinate - goal_y) ** 2) ** 0.5
        
        # Calculate angle (0 is straight on, 90 is from side)
        angle = 0.0
        if x_coordinate != goal_x:  # Avoid division by zero
            angle = abs(math.degrees(math.atan((y_coordinate - goal_y) / (x_coordinate - goal_x))))
        else:
            angle = 90.0
        
        # Simple xG model based on distance and angle
        base_xg = max(0.01, 1.0 - (distance / 100.0))
        angle_factor = angle / 90.0  # Normalize angle to 0-1
        xg = base_xg * (1.0 - (angle_factor * 0.7))
        
        return min(0.95, xg)  # Cap at 0.95

    # Add this method after the calculate_pri method:
    def calculate_pdi(self, player_id=None, team_id=None, game_id=None):
        """
        Calculate Positional Disruption Index:
        Weighted sum of broken pass chains, entry denials, cycle cuts
        """
        pdi_score = 0.0
        
        # 1. Count intercepted passes
        pass_query = self.db.query(Pass).filter(Pass.intercepted == True)
        
        # Apply filters
        if player_id:
            pass_query = pass_query.filter(Pass.intercepted_by_id == player_id)
        if team_id or game_id:
            pass_query = pass_query.join(GameEvent, Pass.event_id == GameEvent.id)
            if team_id:
                pass_query = pass_query.filter(GameEvent.team_id == team_id)
            if game_id:
                pass_query = pass_query.filter(GameEvent.game_id == game_id)
        
        intercepted_passes = pass_query.count()
        pdi_score += intercepted_passes * 1.5  # Weight for pass interceptions
        
        # 2. Count takeaways (active turnovers caused)
        takeaway_query = self.db.query(PuckRecovery).filter(PuckRecovery.recovery_type == "takeaway")
        if player_id:
            takeaway_query = takeaway_query.filter(PuckRecovery.player_id == player_id)
        if team_id or game_id:
            takeaway_query = takeaway_query.join(GameEvent, PuckRecovery.event_id == GameEvent.id)
            if team_id:
                takeaway_query = takeaway_query.filter(GameEvent.team_id == team_id)
            if game_id:
                takeaway_query = takeaway_query.filter(GameEvent.game_id == game_id)
        
        takeaways = takeaway_query.count()
        pdi_score += takeaways * 1.8  # Weight for takeaways
        
        return pdi_score

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
    
    def calculate_player_metrics(self, player_id: int) -> Dict[str, Any]:
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
    
    def calculate_team_metrics(self, team_id: int) -> Dict[str, Any]:
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