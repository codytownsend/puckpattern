"""
Process raw game events into specialized analytics tables.
"""
import logging
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session

from app.models.base import GameEvent
from app.models.analytics import (
    ShotEvent, ZoneEntry, Pass, PuckRecovery, 
    Shift, PowerPlay, PlayerGameStats, TeamGameStats
)

logger = logging.getLogger(__name__)

class EventProcessor:
    """Process raw game events into specialized analytics tables."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def process_game(self, game_id: str) -> Dict[str, int]:
        """
        Process all events for a game.
        
        Args:
            game_id: Game ID to process
            
        Returns:
            Stats about processed events
        """
        # Get all events for this game, ordered by time
        events = self.db.query(GameEvent).filter(
            GameEvent.game_id == game_id
        ).order_by(
            GameEvent.period, 
            GameEvent.time_elapsed
        ).all()
        
        # Initialize counters
        stats = {
            "total_events": len(events),
            "shots_processed": 0,
            "entries_processed": 0,
            "passes_processed": 0,
            "recoveries_processed": 0
        }
        
        # Process each event
        for event in events:
            # Skip already processed events
            if self._is_processed(event):
                continue
                
            # Process based on event type
            if event.event_type in ["shot", "shot-on-goal", "goal", "missed-shot", "blocked-shot"]:
                self._process_shot(event)
                stats["shots_processed"] += 1
                
            elif "entry" in event.event_type.lower() or self._is_zone_entry(event):
                self._process_zone_entry(event)
                stats["entries_processed"] += 1
                
            elif "pass" in event.event_type.lower():
                self._process_pass(event)
                stats["passes_processed"] += 1
                
            elif event.event_type in ["takeaway", "recovery"]:
                self._process_recovery(event)
                stats["recoveries_processed"] += 1
        
        # After processing all events, create derived data
        self._calculate_player_stats(game_id)
        self._calculate_team_stats(game_id)
        
        return stats
    
    def _is_processed(self, event: GameEvent) -> bool:
        """
        Check if an event has already been processed into specialized tables.
        
        Args:
            event: The game event to check
            
        Returns:
            True if already processed, False otherwise
        """
        # Check for shot events
        if event.event_type in ["shot", "shot-on-goal", "goal", "missed-shot", "blocked-shot"]:
            shot = self.db.query(ShotEvent).filter(ShotEvent.event_id == event.id).first()
            return shot is not None
            
        # Check for zone entries
        elif "entry" in event.event_type.lower():
            entry = self.db.query(ZoneEntry).filter(ZoneEntry.event_id == event.id).first()
            return entry is not None
            
        # Check for passes
        elif "pass" in event.event_type.lower():
            pass_event = self.db.query(Pass).filter(Pass.event_id == event.id).first()
            return pass_event is not None
            
        # Check for recoveries
        elif event.event_type in ["takeaway", "recovery"]:
            recovery = self.db.query(PuckRecovery).filter(PuckRecovery.event_id == event.id).first()
            return recovery is not None
            
        # Not a processable event type
        return True
    
    def _is_zone_entry(self, event: GameEvent) -> bool:
        """
        Detect if an event should be classified as a zone entry even if not explicitly labeled.
        
        Args:
            event: The game event to check
            
        Returns:
            True if it represents a zone entry, False otherwise
        """
        # Check for explicit entry events first
        if "entry" in event.event_type.lower():
            return True
            
        # Look for certain patterns that indicate entry
        # 1. Check for rapid movement into offensive zone
        if event.x_coordinate is not None and event.x_coordinate > 25:
            # Look for a previous event by this team in neutral/defensive zone
            prev_event = self.db.query(GameEvent).filter(
                GameEvent.game_id == event.game_id,
                GameEvent.period == event.period,
                GameEvent.time_elapsed < event.time_elapsed,
                GameEvent.time_elapsed >= event.time_elapsed - 5,  # Within 5 seconds
                GameEvent.team_id == event.team_id,
                GameEvent.x_coordinate <= 25  # Neutral or defensive zone
            ).order_by(GameEvent.time_elapsed.desc()).first()
            
            if prev_event:
                # This seems to be a zone entry
                return True
                
        # 2. Check for first possession in offensive zone
        if event.event_type in ["shot", "shot-on-goal", "pass"] and event.x_coordinate is not None and event.x_coordinate > 25:
            # Look for a previous event by the team
            prev_team_event = self.db.query(GameEvent).filter(
                GameEvent.game_id == event.game_id,
                GameEvent.period == event.period,
                GameEvent.time_elapsed < event.time_elapsed,
                GameEvent.time_elapsed >= event.time_elapsed - 3,  # Within 3 seconds
                GameEvent.team_id == event.team_id
            ).order_by(GameEvent.time_elapsed.desc()).first()
            
            # If no previous team event, this might be first possession in zone
            if not prev_team_event:
                return True
                
        return False
    
    def _process_shot(self, event: GameEvent) -> None:
        """
        Process shot events into the shot_events table.
        
        Args:
            event: The shot event to process
        """
        # Skip if already processed
        existing = self.db.query(ShotEvent).filter(ShotEvent.event_id == event.id).first()
        if existing:
            return
            
        # Determine shot result
        is_goal = event.event_type == "goal"
        
        # Determine shot type
        # You might have this in event details or need to infer it
        shot_type = "wrist_shot"  # Default
        if hasattr(event, "details") and event.details:
            shot_type = event.details.get("shotType", "wrist_shot")
            
        # Calculate distance and angle if coordinates available
        distance = None
        angle = None
        if event.x_coordinate is not None and event.y_coordinate is not None:
            # Assuming NHL coordinate system
            goal_x = 89  # X-coordinate of goal line
            goal_y = 0   # Y-coordinate of center of goal
            
            # Calculate distance in feet
            distance = ((event.x_coordinate - goal_x) ** 2 + (event.y_coordinate - goal_y) ** 2) ** 0.5
            
            # Calculate angle (0 is straight on, 90 is from side)
            if event.x_coordinate != goal_x:  # Avoid division by zero
                angle = abs(math.degrees(math.atan((event.y_coordinate - goal_y) / (event.x_coordinate - goal_x))))
            else:
                angle = 90
                
        # Get shooter (already in event)
        shooter_id = event.player_id
        
        # Look for goalie (might be in event details or need to infer)
        goalie_id = None
        if hasattr(event, "details") and event.details and "goalieId" in event.details:
            goalie_id = event.details["goalieId"]
        
        # For goals, look for assists
        primary_assist_id = None
        secondary_assist_id = None
        if is_goal:
            # Check event details for assists
            if hasattr(event, "details") and event.details:
                if "primaryAssistId" in event.details:
                    primary_assist_id = event.details["primaryAssistId"]
                if "secondaryAssistId" in event.details:
                    secondary_assist_id = event.details["secondaryAssistId"]
        
        # Look for preceding event for context
        preceding_event_id = None
        prev_event = self.db.query(GameEvent).filter(
            GameEvent.game_id == event.game_id,
            GameEvent.period == event.period,
            GameEvent.time_elapsed < event.time_elapsed,
            GameEvent.time_elapsed >= event.time_elapsed - 3  # Within 3 seconds
        ).order_by(GameEvent.time_elapsed.desc()).first()
        
        if prev_event:
            preceding_event_id = prev_event.id
        
        # Create shot event record
        shot_event = ShotEvent(
            event_id=event.id,
            shot_type=shot_type,
            distance=distance,
            angle=angle,
            goal=is_goal,
            shooter_id=shooter_id,
            goalie_id=goalie_id,
            primary_assist_id=primary_assist_id,
            secondary_assist_id=secondary_assist_id,
            preceding_event_id=preceding_event_id,
            xg=self._calculate_xg(distance, angle, shot_type),  # Calculate expected goals
            is_scoring_chance=self._is_scoring_chance(distance, angle),
            is_high_danger=self._is_high_danger(distance, angle),
            rush_shot=self._is_rush_shot(event, preceding_event_id),
            rebound_shot=self._is_rebound_shot(event, preceding_event_id)
        )
        
        self.db.add(shot_event)
        self.db.commit()

    def _calculate_xg(self, distance: Optional[float], angle: Optional[float], shot_type: str) -> float:
        """Calculate expected goal value for a shot."""
        if distance is None or angle is None:
            return 0.05  # Default xG if missing coordinates
            
        # Simple model: closer shots and shots with better angles have higher xG
        # This is a simplified placeholder - a real xG model would be more complex
        base_xg = max(0.01, 1.0 - (distance / 100))
        angle_factor = angle / 90.0  # Normalize angle to 0-1
        
        xg = base_xg * (1.0 - (angle_factor * 0.7))
        
        # Adjust for shot type
        type_multipliers = {
            "wrist_shot": 1.0,
            "slap_shot": 0.9,
            "snap_shot": 1.0,
            "backhand": 0.85,
            "deflection": 1.3,
            "tip_in": 1.4,
            "one_timer": 1.2
        }
        
        multiplier = type_multipliers.get(shot_type.lower().replace(" ", "_"), 1.0)
        xg *= multiplier
        
        return min(0.95, xg)  # Cap at 0.95

    def _is_scoring_chance(self, distance: Optional[float], angle: Optional[float]) -> bool:
        """Determine if a shot is a scoring chance based on location."""
        if distance is None or angle is None:
            return False
            
        # Simple rule: shots within 30 feet or with good angle are scoring chances
        return distance <= 30 or angle <= 30

    def _is_high_danger(self, distance: Optional[float], angle: Optional[float]) -> bool:
        """Determine if a shot is from a high-danger area."""
        if distance is None or angle is None:
            return False
            
        # Simple rule: shots within 15 feet or with excellent angle are high danger
        return distance <= 15 or angle <= 15

    def _is_rush_shot(self, event: GameEvent, preceding_event_id: Optional[int]) -> bool:
        """Determine if a shot was taken on a rush play."""
        if preceding_event_id is None:
            return False
            
        # Get preceding event
        prev_event = self.db.query(GameEvent).get(preceding_event_id)
        if not prev_event:
            return False
            
        # If previous event was in neutral zone and within 5 seconds, likely a rush
        if prev_event.x_coordinate is not None and -25 <= prev_event.x_coordinate <= 25:
            time_diff = event.time_elapsed - prev_event.time_elapsed
            return time_diff <= 5.0
            
        return False

    def _is_rebound_shot(self, event: GameEvent, preceding_event_id: Optional[int]) -> bool:
        """Determine if a shot was a rebound."""
        if preceding_event_id is None:
            return False
            
        # Get preceding event
        prev_event = self.db.query(GameEvent).get(preceding_event_id)
        if not prev_event:
            return False
            
        # If previous event was a shot and within 3 seconds, likely a rebound
        if prev_event.event_type in ["shot", "shot-on-goal", "missed-shot"]:
            time_diff = event.time_elapsed - prev_event.time_elapsed
            return time_diff <= 3.0
            
        return False
    
    def _process_zone_entry(self, event: GameEvent) -> None:
        """
        Process zone entry events into the zone_entries table.
        
        Args:
            event: The entry event to process
        """
        # Skip if already processed
        existing = self.db.query(ZoneEntry).filter(ZoneEntry.event_id == event.id).first()
        if existing:
            return
            
        # Determine entry type and if controlled
        entry_type = "carry"  # Default
        controlled = True     # Default
        
        # Check event details if available
        if hasattr(event, "details") and event.details:
            if "entryType" in event.details:
                entry_type = event.details["entryType"]
            if "controlled" in event.details:
                controlled = event.details["controlled"]
        else:
            # Infer from event text/description if available
            if hasattr(event, "description"):
                description = event.description.lower()
                if "dump" in description:
                    entry_type = "dump"
                    controlled = False
                elif "pass" in description:
                    entry_type = "pass"
                    controlled = True
        
        # Get player (already in event)
        player_id = event.player_id
        
        # Try to identify defender
        defender_id = None
        if hasattr(event, "details") and event.details and "defenderId" in event.details:
            defender_id = event.details["defenderId"]
        
        # Check if this entry led to a shot
        led_to_shot = False
        shot_time = None
        
        # Look for shot within 10 seconds
        next_shot = self.db.query(GameEvent).filter(
            GameEvent.game_id == event.game_id,
            GameEvent.period == event.period,
            GameEvent.time_elapsed > event.time_elapsed,
            GameEvent.time_elapsed <= event.time_elapsed + 10,  # Within 10 seconds
            GameEvent.team_id == event.team_id,
            GameEvent.event_type.in_(["shot", "shot-on-goal", "goal", "missed-shot"])
        ).order_by(GameEvent.time_elapsed).first()
        
        if next_shot:
            led_to_shot = True
            shot_time = next_shot.time_elapsed - event.time_elapsed
        
        # Determine if it was a rush entry
        attack_speed = "CONTROLLED"  # Default
        if self._is_rush_entry(event):
            attack_speed = "RUSH"
        
        # Create zone entry record
        zone_entry = ZoneEntry(
            event_id=event.id,
            entry_type=entry_type,
            controlled=controlled,
            player_id=player_id,
            defender_id=defender_id,
            lead_to_shot=led_to_shot,
            lead_to_shot_time=shot_time,
            attack_speed=attack_speed
        )
        
        self.db.add(zone_entry)
        self.db.commit()

    def _is_rush_entry(self, event: GameEvent) -> bool:
        """Determine if a zone entry was a rush."""
        # Look for previous events in neutral/defensive zone
        prev_events = self.db.query(GameEvent).filter(
            GameEvent.game_id == event.game_id,
            GameEvent.period == event.period,
            GameEvent.time_elapsed < event.time_elapsed,
            GameEvent.time_elapsed >= event.time_elapsed - 5,  # Within 5 seconds
            GameEvent.team_id == event.team_id
        ).order_by(GameEvent.time_elapsed.desc()).all()
        
        # If previous event was in neutral/defensive zone, and time diff is small, it's a rush
        if prev_events:
            for prev_event in prev_events:
                if prev_event.x_coordinate is not None:
                    # If we see zone progression from DZ/NZ to OZ in < 5 seconds, it's a rush
                    if prev_event.x_coordinate < 0:  # From defensive zone
                        return True
                    elif -25 <= prev_event.x_coordinate <= 25:  # From neutral zone
                        time_diff = event.time_elapsed - prev_event.time_elapsed
                        return time_diff <= 4.0  # Faster transitions indicate rush
        
        return False
    
    def _process_pass(self, event: GameEvent) -> None:
        """
        Process pass events into the passes table.
        
        Args:
            event: The pass event to process
        """
        # Skip if already processed
        existing = self.db.query(Pass).filter(Pass.event_id == event.id).first()
        if existing:
            return
            
        # Get passer (already in event)
        passer_id = event.player_id
        
        # Determine recipient (might be in event details or need to infer)
        recipient_id = None
        if hasattr(event, "details") and event.details and "recipientId" in event.details:
            recipient_id = event.details["recipientId"]
        else:
            # Try to infer recipient from next event
            next_event = self.db.query(GameEvent).filter(
                GameEvent.game_id == event.game_id,
                GameEvent.period == event.period,
                GameEvent.time_elapsed > event.time_elapsed,
                GameEvent.time_elapsed <= event.time_elapsed + 2,  # Within 2 seconds
                GameEvent.team_id == event.team_id,
                GameEvent.player_id != event.player_id  # Different player
            ).order_by(GameEvent.time_elapsed).first()
            
            if next_event:
                recipient_id = next_event.player_id
        
        # Determine pass type
        pass_type = "direct"  # Default
        if hasattr(event, "details") and event.details and "passType" in event.details:
            pass_type = event.details["passType"]
        
        # Determine zone
        zone = "NZ"  # Default to neutral zone
        if event.x_coordinate is not None:
            if event.x_coordinate > 25:
                zone = "OZ"  # Offensive zone
            elif event.x_coordinate < -25:
                zone = "DZ"  # Defensive zone
        
        # Determine if completed
        completed = True  # Default
        if hasattr(event, "details") and event.details and "completed" in event.details:
            completed = event.details["completed"]
        elif recipient_id is None:
            completed = False
        
        # Check for interception
        intercepted = False
        intercepted_by_id = None
        if not completed:
            # Look for possession by opponent within 2 seconds
            next_opponent_event = self.db.query(GameEvent).filter(
                GameEvent.game_id == event.game_id,
                GameEvent.period == event.period,
                GameEvent.time_elapsed > event.time_elapsed,
                GameEvent.time_elapsed <= event.time_elapsed + 2,  # Within 2 seconds
                GameEvent.team_id != event.team_id  # Opponent team
            ).order_by(GameEvent.time_elapsed).first()
            
            if next_opponent_event:
                intercepted = True
                intercepted_by_id = next_opponent_event.player_id
        
        # Calculate distance and angle change if coordinates available
        distance = None
        angle_change = None
        # For this we'd need coordinates of both the pass origin and destination
        # This would require more advanced tracking data
        
        # Create pass record
        pass_event = Pass(
            event_id=event.id,
            passer_id=passer_id,
            recipient_id=recipient_id,
            pass_type=pass_type,
            zone=zone,
            completed=completed,
            intercepted=intercepted,
            intercepted_by_id=intercepted_by_id,
            distance=distance,
            angle_change=angle_change
        )
        
        self.db.add(pass_event)
        self.db.commit()
    
    def _process_recovery(self, event: GameEvent) -> None:
        """
        Process recovery events into the puck_recoveries table.
        
        Args:
            event: The recovery event to process
        """
        # Skip if already processed
        existing = self.db.query(PuckRecovery).filter(PuckRecovery.event_id == event.id).first()
        if existing:
            return
            
        # Get player (already in event)
        player_id = event.player_id
        
        # Determine zone
        zone = "NZ"  # Default to neutral zone
        if event.x_coordinate is not None:
            if event.x_coordinate > 25:
                zone = "OZ"  # Offensive zone
            elif event.x_coordinate < -25:
                zone = "DZ"  # Defensive zone
        
        # Determine recovery type
        recovery_type = "loose"  # Default
        if event.event_type == "takeaway":
            recovery_type = "takeaway"
        elif "forecheck" in (event.description.lower() if hasattr(event, "description") else ""):
            recovery_type = "forecheck"
        
        # Determine if led to possession
        led_to_possession = True  # Default
        
        # Look for subsequent event by same team
        next_team_event = self.db.query(GameEvent).filter(
            GameEvent.game_id == event.game_id,
            GameEvent.period == event.period,
            GameEvent.time_elapsed > event.time_elapsed,
            GameEvent.time_elapsed <= event.time_elapsed + 3,  # Within 3 seconds
            GameEvent.team_id == event.team_id
        ).order_by(GameEvent.time_elapsed).first()
        
        if not next_team_event:
            led_to_possession = False
        
        # Check for preceding event
        preceded_by_id = None
        prev_event = self.db.query(GameEvent).filter(
            GameEvent.game_id == event.game_id,
            GameEvent.period == event.period,
            GameEvent.time_elapsed < event.time_elapsed,
            GameEvent.time_elapsed >= event.time_elapsed - 3  # Within 3 seconds
        ).order_by(GameEvent.time_elapsed.desc()).first()
        
        if prev_event:
            preceded_by_id = prev_event.id
        
        # Create recovery record
        recovery = PuckRecovery(
            event_id=event.id,
            player_id=player_id,
            zone=zone,
            recovery_type=recovery_type,
            lead_to_possession=led_to_possession,
            preceded_by_id=preceded_by_id
        )
        
        self.db.add(recovery)
        self.db.commit()
    
    def _calculate_player_stats(self, game_id: str) -> None:
        """
        Calculate and store player statistics for a game.
        
        Args:
            game_id: Game ID to process
        """
        # Get game
        game = self.db.query(Game).filter(Game.game_id == game_id).first()
        if not game:
            return
            
        # Get players involved in this game
        player_ids = set()
        
        # Add players from events
        events = self.db.query(GameEvent).filter(GameEvent.game_id == game_id).all()
        for event in events:
            if event.player_id:
                player_ids.add(event.player_id)
        
        # Process each player
        for player_id in player_ids:
            # Skip if already processed
            existing = self.db.query(PlayerGameStats).filter(
                PlayerGameStats.player_id == player_id,
                PlayerGameStats.game_id == game.id
            ).first()
            
            if existing:
                continue
                
            # Get player's team
            player = self.db.query(Player).filter(Player.id == player_id).first()
            if not player or not player.team_id:
                continue
                
            # Calculate base stats
            shots = self.db.query(ShotEvent).join(GameEvent).filter(
                GameEvent.game_id == game_id,
                ShotEvent.shooter_id == player_id
            ).count()
            
            goals = self.db.query(ShotEvent).join(GameEvent).filter(
                GameEvent.game_id == game_id,
                ShotEvent.shooter_id == player_id,
                ShotEvent.goal == True
            ).count()
            
            assists = self.db.query(ShotEvent).join(GameEvent).filter(
                GameEvent.game_id == game_id,
                or_(
                    ShotEvent.primary_assist_id == player_id,
                    ShotEvent.secondary_assist_id == player_id
                ),
                ShotEvent.goal == True
            ).count()
            
            # Add other stats here...
            
            # Calculate custom metrics
            ecr = self.calculate_ecr(player_id=player_id, game_id=game_id)
            pri = self.calculate_pri(player_id=player_id, game_id=game_id)
            pdi = self.calculate_pdi(player_id=player_id, game_id=game_id)
            xg_delta_psm = self.calculate_xg_delta_psm(player_id=player_id, game_id=game_id)
            
            # Calculate ICE+ score (example formula)
            ice_plus = (
                (ecr * 1.5) +
                (pri * 1.2) +
                (pdi * 1.0) +
                (xg_delta_psm * 2.0)
            )
            
            # Create player stats record
            player_stats = PlayerGameStats(
                player_id=player_id,
                game_id=game.id,
                team_id=player.team_id,
                shots=shots,
                goals=goals,
                assists=assists,
                # Add other stats here...
                ecr=ecr,
                pri=pri,
                pdi=pdi,
                xg_delta_psm=xg_delta_psm,
                ice_plus=ice_plus
            )
            
            self.db.add(player_stats)
        
        self.db.commit()

    # You'll need to implement these methods (similar to the metrics service)
    def calculate_ecr(self, player_id=None, team_id=None, game_id=None):
        """Calculate Entry Conversion Rate."""
        # Implementation...
        
    def calculate_pri(self, player_id=None, team_id=None, game_id=None):
        """Calculate Puck Recovery Impact."""
        # Implementation...
        
    def calculate_pdi(self, player_id=None, team_id=None, game_id=None):
        """Calculate Positional Disruption Index."""
        # Implementation...
        
    def calculate_xg_delta_psm(self, player_id=None, team_id=None, game_id=None):
        """Calculate Expected Goals Delta from Pass Shot Movement."""
        # Implementation...
    
    def _calculate_team_stats(self, game_id: str) -> None:
        """
        Calculate and store team statistics for a game.
        
        Args:
            game_id: Game ID to process
        """
        # Get game
        game = self.db.query(Game).filter(Game.game_id == game_id).first()
        if not game:
            return
            
        # Process home team
        self._calculate_single_team_stats(game.id, game.home_team_id, game_id)
        
        # Process away team
        self._calculate_single_team_stats(game.id, game.away_team_id, game_id)

    def _calculate_single_team_stats(self, game_db_id: int, team_id: int, game_id: str) -> None:
        """Calculate stats for a single team in a game."""
        # Skip if already processed
        existing = self.db.query(TeamGameStats).filter(
            TeamGameStats.game_id == game_db_id,
            TeamGameStats.team_id == team_id
        ).first()
        
        if existing:
            return
            
        # Calculate base stats
        shots = self.db.query(GameEvent).filter(
            GameEvent.game_id == game_id,
            GameEvent.team_id == team_id,
            GameEvent.event_type.in_(["shot", "shot-on-goal", "goal"])
        ).count()
        
        goals = self.db.query(ShotEvent).join(GameEvent).filter(
            GameEvent.game_id == game_id,
            GameEvent.team_id == team_id,
            ShotEvent.goal == True
        ).count()
        
        # Calculate faceoffs
        faceoff_events = self.db.query(GameEvent).filter(
            GameEvent.game_id == game_id,
            GameEvent.event_type == "faceoff"
        ).all()
        
        faceoff_wins = 0
        faceoff_losses = 0
        
        for faceoff in faceoff_events:
            # You'd need to determine which team won each faceoff
            # This might be in event details or require additional processing
            if hasattr(faceoff, "details") and faceoff.details:
                if faceoff.details.get("winningTeamId") == team_id:
                    faceoff_wins += 1
                else:
                    faceoff_losses += 1
        
        # Calculate custom metrics
        ecr = self.calculate_ecr(team_id=team_id, game_id=game_id)
        pri = self.calculate_pri(team_id=team_id, game_id=game_id)
        pdi = self.calculate_pdi(team_id=team_id, game_id=game_id)
        
        # Detect system types
        forecheck_style = self._detect_forecheck_style(team_id, game_id)
        defensive_structure = self._detect_defensive_structure(team_id, game_id)
        pp_formation = self._detect_pp_formation(team_id, game_id)
        pk_formation = self._detect_pk_formation(team_id, game_id)
        
        # Create team stats record
        team_stats = TeamGameStats(
            team_id=team_id,
            game_id=game_db_id,
            goals=goals,
            shots=shots,
            faceoff_wins=faceoff_wins,
            faceoff_losses=faceoff_losses,
            team_ecr=ecr,
            team_pri=pri,
            team_pdi=pdi,
            forecheck_style=forecheck_style,
            defensive_structure=defensive_structure,
            pp_formation=pp_formation,
            pk_formation=pk_formation
        )
        
        self.db.add(team_stats)
        self.db.commit()

    def _detect_forecheck_style(self, team_id: int, game_id: str) -> str:
        """Detect the team's forecheck style."""
        # Implementation depends on your classification methodology
        # Example: Count recoveries in various zones
        oz_recoveries = self.db.query(PuckRecovery).join(GameEvent).filter(
            GameEvent.game_id == game_id,
            GameEvent.team_id == team_id,
            PuckRecovery.zone == "OZ"
        ).count()
        
        nz_recoveries = self.db.query(PuckRecovery).join(GameEvent).filter(
            GameEvent.game_id == game_id,
            GameEvent.team_id == team_id,
            PuckRecovery.zone == "NZ"
        ).count()
        
        if oz_recoveries > 2 * nz_recoveries:
            return "AGGRESSIVE"
        elif oz_recoveries > nz_recoveries:
            return "STANDARD"
        else:
            return "PASSIVE"

    def _detect_defensive_structure(self, team_id: int, game_id: str) -> str:
        """Detect the team's defensive structure."""
        # Implementation depends on your classification methodology
        return "MAN_ON_MAN"  # Example

    def _detect_pp_formation(self, team_id: int, game_id: str) -> str:
        """Detect the team's power play formation."""
        # Implementation depends on your classification methodology
        return "1-3-1"  # Example

    def _detect_pk_formation(self, team_id: int, game_id: str) -> str:
        """Detect the team's penalty kill formation."""
        # Implementation depends on your classification methodology
        return "DIAMOND"  # Example