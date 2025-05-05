from typing import Dict, List, Optional, Any
import numpy as np
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func

from app.models.base import GameEvent, Team, Player, Game
from app.models.analytics import ShotEvent
from app.schemas.shot import HeatmapPoint, ShotHeatmapResponse


class ShotAnalysisService:
    """
    Service for analyzing shot data and generating visualizations.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def _get_filtered_shots(self, filters: Dict[str, Any]) -> List[ShotEvent]:
        """
        Get filtered shots from the database.
        """
        query = self.db.query(ShotEvent).join(GameEvent)
        
        if filters.get("team_id"):
            query = query.filter(GameEvent.team_id == filters["team_id"])
        
        if filters.get("player_id"):
            query = query.filter(ShotEvent.shooter_id == filters["player_id"])
        
        if filters.get("game_id"):
            query = query.filter(GameEvent.game_id == filters["game_id"])
        
        if filters.get("season"):
            query = query.join(Game, GameEvent.game_id == Game.game_id).filter(Game.season == filters["season"])
        
        if filters.get("shot_type"):
            query = query.filter(ShotEvent.shot_type == filters["shot_type"])
        
        if filters.get("goal_only"):
            query = query.filter(ShotEvent.goal == True)
        
        return query.all()
    
    def generate_heatmap(self, filters: Dict[str, Any], normalize: bool = True) -> ShotHeatmapResponse:
        """
        Generate a shot heatmap for visualization.
        """
        shots = self._get_filtered_shots(filters)
        
        if not shots:
            return ShotHeatmapResponse(
                points=[],
                max_value=0,
                total_shots=0,
                total_goals=0,
                average_xg=0,
                metadata={"filters": filters}
            )
        
        # Process shot locations into a 2D grid
        grid_size = 10  # 10 ft grid cells
        rink_length = 200
        rink_width = 85
        
        # Create a grid to count shots
        grid = np.zeros((int(rink_width / grid_size) + 1, int(rink_length / grid_size) + 1))
        
        for shot in shots:
            # Convert coordinates to grid indices
            event = shot.event
            x_idx = int(event.x_coordinate / grid_size)
            y_idx = int(event.y_coordinate / grid_size)
            
            # Ensure within bounds
            if 0 <= x_idx < grid.shape[1] and 0 <= y_idx < grid.shape[0]:
                grid[y_idx, x_idx] += 1
        
        # Generate heatmap points
        points = []
        max_value = np.max(grid)
        
        for y_idx in range(grid.shape[0]):
            for x_idx in range(grid.shape[1]):
                value = grid[y_idx, x_idx]
                if value > 0:
                    # Convert back to coordinate space
                    x = x_idx * grid_size + (grid_size / 2)  # Center of the cell
                    y = y_idx * grid_size + (grid_size / 2)
                    
                    # Normalize if requested
                    if normalize and max_value > 0:
                        value = value / max_value
                    
                    points.append(HeatmapPoint(x=x, y=y, value=float(value)))
        
        # Calculate stats
        total_shots = len(shots)
        total_goals = sum(1 for shot in shots if shot.goal)
        average_xg = sum(shot.xg or 0 for shot in shots) / total_shots if total_shots > 0 else 0
        
        return ShotHeatmapResponse(
            points=points,
            max_value=float(max_value),
            total_shots=total_shots,
            total_goals=total_goals,
            average_xg=average_xg,
            metadata={
                "filters": filters,
                "grid_size": grid_size
            }
        )
    
    def get_xg_breakdown(self, player_id: str, season: Optional[str] = None) -> Dict[str, Any]:
        """
        Get a detailed breakdown of player's expected goals.
        """
        player = self.db.query(Player).filter(Player.player_id == player_id).first()
        if not player:
            return {"error": "Player not found"}
        
        query = self.db.query(ShotEvent).filter(ShotEvent.shooter_id == player.id)
        
        if season:
            query = query.join(GameEvent).join(Game, GameEvent.game_id == Game.game_id).filter(Game.season == season)
        
        shots = query.all()
        
        # Calculate various xG metrics
        total_shots = len(shots)
        if total_shots == 0:
            return {
                "player_id": player_id,
                "player_name": player.name,
                "season": season,
                "total_shots": 0,
                "total_xg": 0,
                "actual_goals": 0,
                "xg_per_shot": 0,
                "shot_types": {},
                "shot_zones": {},
                "xg_by_period": {}
            }
        
        actual_goals = sum(1 for shot in shots if shot.goal)
        total_xg = sum(shot.xg or 0 for shot in shots)
        xg_per_shot = total_xg / total_shots
        
        # Break down by shot type
        shot_types = {}
        for shot in shots:
            shot_type = shot.shot_type
            if shot_type not in shot_types:
                shot_types[shot_type] = {
                    "count": 0,
                    "xg": 0,
                    "goals": 0
                }
            
            shot_types[shot_type]["count"] += 1
            shot_types[shot_type]["xg"] += shot.xg or 0
            if shot.goal:
                shot_types[shot_type]["goals"] += 1
        
        # Break down by zone (simplified for now)
        shot_zones = {
            "slot": {"count": 0, "xg": 0, "goals": 0},
            "point": {"count": 0, "xg": 0, "goals": 0},
            "left_circle": {"count": 0, "xg": 0, "goals": 0},
            "right_circle": {"count": 0, "xg": 0, "goals": 0},
            "other": {"count": 0, "xg": 0, "goals": 0}
        }
        
        for shot in shots:
            event = shot.event
            x, y = event.x_coordinate, event.y_coordinate
            
            # Determine zone (simplified - would be more detailed in production)
            if 75 <= x <= 125 and 30 <= y <= 55:
                zone = "slot"
            elif x > 140:
                zone = "point"
            elif y < 42.5 and x < 125:
                zone = "left_circle"
            elif y > 42.5 and x < 125:
                zone = "right_circle"
            else:
                zone = "other"
            
            shot_zones[zone]["count"] += 1
            shot_zones[zone]["xg"] += shot.xg or 0
            if shot.goal:
                shot_zones[zone]["goals"] += 1
        
        # Break down by period
        xg_by_period = {}
        for shot in shots:
            period = shot.event.period
            if period not in xg_by_period:
                xg_by_period[period] = {
                    "count": 0,
                    "xg": 0,
                    "goals": 0
                }
            
            xg_by_period[period]["count"] += 1
            xg_by_period[period]["xg"] += shot.xg or 0
            if shot.goal:
                xg_by_period[period]["goals"] += 1
        
        return {
            "player_id": player_id,
            "player_name": player.name,
            "season": season,
            "total_shots": total_shots,
            "total_xg": total_xg,
            "actual_goals": actual_goals,
            "xg_per_shot": xg_per_shot,
            "shot_types": shot_types,
            "shot_zones": shot_zones,
            "xg_by_period": xg_by_period
        }
    
    def compare_team_shot_patterns(self, team_id1: str, team_id2: str, season: Optional[str] = None) -> Dict[str, Any]:
        """
        Compare shot patterns between two teams.
        """
        team1 = self.db.query(Team).filter(Team.team_id == team_id1).first()
        team2 = self.db.query(Team).filter(Team.team_id == team_id2).first()
        
        if not team1 or not team2:
            return {"error": "One or both teams not found"}
        
        team1_filters = {"team_id": team1.id, "season": season}
        team2_filters = {"team_id": team2.id, "season": season}
        
        team1_shots = self._get_filtered_shots(team1_filters)
        team2_shots = self._get_filtered_shots(team2_filters)
        
        # High-level comparison
        t1_total = len(team1_shots)
        t2_total = len(team2_shots)
        
        if t1_total == 0 or t2_total == 0:
            return {
                "error": "Insufficient data for comparison",
                "team1_shots": t1_total,
                "team2_shots": t2_total
            }
        
        # Compare shot distributions and metrics
        t1_goals = sum(1 for shot in team1_shots if shot.goal)
        t2_goals = sum(1 for shot in team2_shots if shot.goal)
        
        t1_xg = sum(shot.xg or 0 for shot in team1_shots)
        t2_xg = sum(shot.xg or 0 for shot in team2_shots)
        
        t1_avg_xg = t1_xg / t1_total
        t2_avg_xg = t2_xg / t2_total
        
        # Shot zone analysis (simplified)
        zones = ["slot", "point", "left_circle", "right_circle", "other"]
        t1_zones = {zone: 0 for zone in zones}
        t2_zones = {zone: 0 for zone in zones}
        
        for shot in team1_shots:
            event = shot.event
            x, y = event.x_coordinate, event.y_coordinate
            
            if 75 <= x <= 125 and 30 <= y <= 55:
                t1_zones["slot"] += 1
            elif x > 140:
                t1_zones["point"] += 1
            elif y < 42.5 and x < 125:
                t1_zones["left_circle"] += 1
            elif y > 42.5 and x < 125:
                t1_zones["right_circle"] += 1
            else:
                t1_zones["other"] += 1
        
        for shot in team2_shots:
            event = shot.event
            x, y = event.x_coordinate, event.y_coordinate
            
            if 75 <= x <= 125 and 30 <= y <= 55:
                t2_zones["slot"] += 1
            elif x > 140:
                t2_zones["point"] += 1
            elif y < 42.5 and x < 125:
                t2_zones["left_circle"] += 1
            elif y > 42.5 and x < 125:
                t2_zones["right_circle"] += 1
            else:
                t2_zones["other"] += 1
        
        # Convert to percentages
        t1_zone_pct = {zone: count / t1_total for zone, count in t1_zones.items()}
        t2_zone_pct = {zone: count / t2_total for zone, count in t2_zones.items()}
        
        # Shot type analysis
        shot_types = set()
        for shot in team1_shots + team2_shots:
            shot_types.add(shot.shot_type)
        
        t1_types = {stype: 0 for stype in shot_types}
        t2_types = {stype: 0 for stype in shot_types}
        
        for shot in team1_shots:
            t1_types[shot.shot_type] += 1
        
        for shot in team2_shots:
            t2_types[shot.shot_type] += 1
        
        # Convert to percentages
        t1_type_pct = {stype: count / t1_total for stype, count in t1_types.items()}
        t2_type_pct = {stype: count / t2_total for stype, count in t2_types.items()}
        
        return {
            "team1": {
                "id": team_id1,
                "name": team1.name,
                "shots": t1_total,
                "goals": t1_goals,
                "xg": t1_xg,
                "avg_xg_per_shot": t1_avg_xg,
                "zone_distribution": t1_zone_pct,
                "shot_type_distribution": t1_type_pct
            },
            "team2": {
                "id": team_id2,
                "name": team2.name,
                "shots": t2_total,
                "goals": t2_goals,
                "xg": t2_xg,
                "avg_xg_per_shot": t2_avg_xg,
                "zone_distribution": t2_zone_pct,
                "shot_type_distribution": t2_type_pct
            },
            "comparison": {
                "shot_volume_diff": t1_total - t2_total,
                "goal_diff": t1_goals - t2_goals,
                "xg_diff": t1_xg - t2_xg,
                "avg_xg_diff": t1_avg_xg - t2_avg_xg,
                "zone_diff": {zone: t1_zone_pct[zone] - t2_zone_pct[zone] for zone in zones},
                "shot_type_diff": {stype: t1_type_pct.get(stype, 0) - t2_type_pct.get(stype, 0) for stype in shot_types}
            }
        }
    
    def get_player_dangerous_zones(self, player_id: str, season: Optional[str] = None) -> Dict[str, Any]:
        """
        Get zones where a player is most dangerous (highest xG).
        """
        player = self.db.query(Player).filter(Player.player_id == player_id).first()
        if not player:
            return {"error": "Player not found"}
        
        filters = {"player_id": player.id, "season": season}
        shots = self._get_filtered_shots(filters)
        
        if not shots:
            return {
                "player_id": player_id,
                "player_name": player.name,
                "season": season,
                "total_shots": 0,
                "zones": []
            }
        
        # Define zones (would be more sophisticated in production)
        zones = {
            "slot": {"x_min": 75, "x_max": 125, "y_min": 30, "y_max": 55, "shots": [], "xg": 0, "goals": 0},
            "left_circle": {"x_min": 0, "x_max": 125, "y_min": 0, "y_max": 42.5, "shots": [], "xg": 0, "goals": 0},
            "right_circle": {"x_min": 0, "x_max": 125, "y_min": 42.5, "y_max": 85, "shots": [], "xg": 0, "goals": 0},
            "point": {"x_min": 125, "x_max": 200, "y_min": 0, "y_max": 85, "shots": [], "xg": 0, "goals": 0},
            "net_front": {"x_min": 80, "x_max": 100, "y_min": 35, "y_max": 50, "shots": [], "xg": 0, "goals": 0}
        }
        
        # Categorize shots by zone
        for shot in shots:
            event = shot.event
            x, y = event.x_coordinate, event.y_coordinate
            
            for zone_name, zone_info in zones.items():
                if (zone_info["x_min"] <= x <= zone_info["x_max"] and 
                    zone_info["y_min"] <= y <= zone_info["y_max"]):
                    zone_info["shots"].append(shot)
                    zone_info["xg"] += shot.xg or 0
                    if shot.goal:
                        zone_info["goals"] += 1
        
        # Calculate danger metrics for each zone
        zone_metrics = []
        for zone_name, zone_info in zones.items():
            num_shots = len(zone_info["shots"])
            if num_shots == 0:
                continue
            
            avg_xg = zone_info["xg"] / num_shots
            shooting_pct = (zone_info["goals"] / num_shots) * 100 if num_shots > 0 else 0
            
            zone_metrics.append({
                "zone": zone_name,
                "shots": num_shots,
                "goals": zone_info["goals"],
                "total_xg": zone_info["xg"],
                "avg_xg": avg_xg,
                "shooting_pct": shooting_pct,
                "danger_score": avg_xg * num_shots  # Simple danger metric
            })
        
        # Sort by danger score
        zone_metrics.sort(key=lambda x: x["danger_score"], reverse=True)
        
        return {
            "player_id": player_id,
            "player_name": player.name,
            "season": season,
            "total_shots": len(shots),
            "zones": zone_metrics
        }