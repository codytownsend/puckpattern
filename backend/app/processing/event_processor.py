"""
Process raw game events into specialized analytics tables.
"""
import logging
import math
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session

from app.models.base import GameEvent, Player
from app.models.analytics import (
    Game, ShotEvent, ZoneEntry, Pass, PuckRecovery, 
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
        # Get the game
        game = self.db.query(Game).filter(Game.game_id == game_id).first()
        if not game:
            return {"error": f"Game {game_id} not found"}
        
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
            "recoveries_processed": 0,
            "other_processed": 0
        }
        
        # Process each event
        for event in events:
            # Skip already processed events
            if self._is_processed(event):
                continue
                
            # Process based on exact event types we found
            event_type = event.event_type.lower() if event.event_type else ""
            
            # Shot-related events
            if event_type in ["shot-on-goal", "blocked-shot", "missed-shot", "goal", "failed-shot-attempt"]:
                self._process_shot(event)
                stats["shots_processed"] += 1
            
            # Recovery events    
            elif event_type in ["giveaway", "takeaway"]:
                self._process_recovery(event)
                stats["recoveries_processed"] += 1
            
            # Zone entries need to be inferred (not in explicit events)
            elif self._is_zone_entry(event):
                self._process_zone_entry(event)
                stats["entries_processed"] += 1
            
            # Passes need to be inferred (not in explicit events)
            elif self._is_pass(event):
                self._process_pass(event)
                stats["passes_processed"] += 1
            
            # Other events that might be useful for context
            elif event_type in ["faceoff", "hit", "penalty", "delayed-penalty"]:
                # Process other events that provide context
                if event_type == "faceoff":
                    self._process_faceoff(event)
                elif event_type == "hit":
                    self._process_hit(event)
                elif event_type in ["penalty", "delayed-penalty"]:
                    self._process_penalty(event)
                
                stats["other_processed"] += 1
        
        # After processing all events, calculate derived data
        self._calculate_player_stats(game_id)
        self._calculate_team_stats(game_id)
        
        # Commit all changes
        self.db.commit()
        
        return stats
    
    def _is_pass(self, event: GameEvent) -> bool:
        """
        Infer if an event is a pass based on context.
        Since we don't have explicit pass events, we need to infer them.
        
        Args:
            event: The game event
            
        Returns:
            True if likely a pass, False otherwise
        """
        # This is a placeholder - in a real implementation, you'd look at:
        # 1. Consecutive possession events by different players on same team
        # 2. Event descriptions that might mention passes
        # 3. Player position changes that suggest passes
        
        # For now, we'll return False to avoid creating inaccurate pass data
        return False
    
    def _process_shot(self, event: GameEvent) -> Optional[ShotEvent]:
        """
        Process shot events (shot-on-goal, blocked-shot, missed-shot, goal)
        
        Args:
            event: The shot event
            
        Returns:
            Created shot event or None
        """
        # Skip if already processed
        existing = self.db.query(ShotEvent).filter(ShotEvent.event_id == event.id).first()
        if existing:
            return existing
        
        # Determine if it's a goal
        is_goal = (event.event_type.lower() == "goal")
        
        # Get shot type from event type
        shot_type = event.event_type.lower().replace("-", "_")
        
        # Calculate distance and angle if coordinates available
        distance = None
        angle = None
        if event.x_coordinate is not None and event.y_coordinate is not None:
            # NHL coordinates: center ice is 0,0, goal lines at +/-89 feet
            goal_x = 89  # This might need to be adjusted based on your data
            goal_y = 0
            
            # Calculate distance in feet
            distance = ((event.x_coordinate - goal_x) ** 2 + (event.y_coordinate - goal_y) ** 2) ** 0.5
            
            # Calculate angle (0 is straight on, 90 is from side)
            if event.x_coordinate != goal_x:  # Avoid division by zero
                angle = abs(math.degrees(math.atan((event.y_coordinate - goal_y) / (event.x_coordinate - goal_x))))
            else:
                angle = 90.0
        
        # Create shot event
        shot_event = ShotEvent(
            event_id=event.id,
            shot_type=shot_type,
            distance=distance,
            angle=angle,
            goal=is_goal,
            shooter_id=event.player_id,
            # Other fields would be set if available
            xg=self._calculate_xg(distance, angle, shot_type)
        )
        
        self.db.add(shot_event)
        self.db.flush()  # Save but don't commit yet
        
        return shot_event

    def _is_processed(self, event: GameEvent) -> bool:
        """
        Check if an event has already been processed into specialized tables.
        
        Args:
            event: The game event to check
            
        Returns:
            True if already processed, False otherwise
        """
        # Normalize event type to lowercase
        event_type = event.event_type.lower() if event.event_type else ""
        
        # Check for shot events - use the same list as process_game
        if event_type in ["shot-on-goal", "blocked-shot", "missed-shot", "goal", "failed-shot-attempt"]:
            shot = self.db.query(ShotEvent).filter(ShotEvent.event_id == event.id).first()
            return shot is not None
            
        # Check for zone entries - normalize lowercase check
        elif "entry" in event_type:
            entry = self.db.query(ZoneEntry).filter(ZoneEntry.event_id == event.id).first()
            return entry is not None
            
        # Check for passes - already using lowercase check
        elif "pass" in event_type:
            pass_event = self.db.query(Pass).filter(Pass.event_id == event.id).first()
            return pass_event is not None
            
        # Check for recoveries - use consistent list with process_game
        elif event_type in ["giveaway", "takeaway"]:
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

    def calculate_ecr(self, player_id=None, team_id=None, game_id=None):
        """
        Calculate Entry Conversion Rate: 
        # of controlled entries leading to a shot/chance within 10s / total controlled entries
        
        Args:
            player_id: Filter by player ID
            team_id: Filter by team ID
            game_id: Filter by game ID
            
        Returns:
            ECR value (float)
        """
        # Query zone entries
        query = self.db.query(ZoneEntry).filter(ZoneEntry.controlled == True)
        
        # Add game filter if specified
        if game_id:
            # We need to join via GameEvent to filter by game_id
            game = self.db.query(Game).filter(Game.id == game_id).first()
            if game:
                query = query.join(GameEvent).filter(GameEvent.game_id == game.game_id)
        
        # Add player filter if specified
        if player_id:
            query = query.filter(ZoneEntry.player_id == player_id)
        
        # Add team filter if specified
        if team_id:
            query = query.join(GameEvent, ZoneEntry.event_id == GameEvent.id).filter(GameEvent.team_id == team_id)
        
        # Get entries
        entries = query.all()
        
        # Calculate rate
        total_entries = len(entries)
        if total_entries == 0:
            return 0.0
            
        successful_entries = sum(1 for entry in entries if entry.lead_to_shot)
        return successful_entries / total_entries

    def calculate_pri(self, player_id=None, team_id=None, game_id=None):
        """
        Calculate Puck Recovery Impact:
        Weighted sum of recoveries based on zone, outcome, and type
        
        Args:
            player_id: Filter by player ID
            team_id: Filter by team ID
            game_id: Filter by game ID
            
        Returns:
            PRI value (float)
        """
        # Query recoveries
        query = self.db.query(PuckRecovery)
        
        # Add game filter if specified
        if game_id:
            # We need to join via GameEvent to filter by game_id
            game = self.db.query(Game).filter(Game.id == game_id).first()
            if game:
                query = query.join(GameEvent, PuckRecovery.event_id == GameEvent.id).filter(GameEvent.game_id == game.game_id)
        
        # Add player filter if specified
        if player_id:
            query = query.filter(PuckRecovery.player_id == player_id)
        
        # Add team filter if specified
        if team_id:
            query = query.join(GameEvent, PuckRecovery.event_id == GameEvent.id).filter(GameEvent.team_id == team_id)
        
        # Get recoveries
        recoveries = query.all()
        
        # Calculate PRI score
        pri_score = 0.0
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

    def calculate_pdi(self, player_id=None, team_id=None, game_id=None):
        """
        Calculate Positional Disruption Index:
        Weighted sum of broken pass chains, entry denials, cycle cuts
        
        Args:
            player_id: Filter by player ID
            team_id: Filter by team ID
            game_id: Filter by game ID
            
        Returns:
            PDI value (float)
        """
        pdi_score = 0.0
        
        # 1. Count intercepted passes
        pass_query = self.db.query(Pass).filter(Pass.intercepted == True)
        if player_id:
            pass_query = pass_query.filter(Pass.intercepted_by_id == player_id)
        if team_id or game_id:
            pass_query = pass_query.join(GameEvent, Pass.event_id == GameEvent.id)
            if team_id:
                pass_query = pass_query.filter(GameEvent.team_id == team_id)
            if game_id:
                game = self.db.query(Game).filter(Game.id == game_id).first()
                if game:
                    pass_query = pass_query.filter(GameEvent.game_id == game.game_id)
        
        intercepted_passes = pass_query.count()
        pdi_score += intercepted_passes * 1.5  # Weight for pass interceptions
        
        # 2. Count entry denials (unsuccessful zone entries against)
        entry_query = self.db.query(ZoneEntry).filter(ZoneEntry.controlled == False)
        if player_id:
            entry_query = entry_query.filter(ZoneEntry.defender_id == player_id)
        if team_id or game_id:
            entry_query = entry_query.join(GameEvent, ZoneEntry.event_id == GameEvent.id)
            if team_id:
                # For entries, need to find entries against this team
                # This is more complex and depends on your data model
                # Simplified: Find entries where the team is defending
                entry_query = entry_query.join(Game, GameEvent.game_id == Game.game_id)
                entry_query = entry_query.filter(
                    or_(
                        and_(Game.home_team_id == team_id, GameEvent.team_id == Game.away_team_id),
                        and_(Game.away_team_id == team_id, GameEvent.team_id == Game.home_team_id)
                    )
                )
            if game_id:
                game = self.db.query(Game).filter(Game.id == game_id).first()
                if game:
                    entry_query = entry_query.filter(GameEvent.game_id == game.game_id)
        
        denied_entries = entry_query.count()
        pdi_score += denied_entries * 2.0  # Weight for entry denials
        
        # 3. Count takeaways (active turnovers caused)
        takeaway_query = self.db.query(PuckRecovery).filter(PuckRecovery.recovery_type == "takeaway")
        if player_id:
            takeaway_query = takeaway_query.filter(PuckRecovery.player_id == player_id)
        if team_id or game_id:
            takeaway_query = takeaway_query.join(GameEvent, PuckRecovery.event_id == GameEvent.id)
            if team_id:
                takeaway_query = takeaway_query.filter(GameEvent.team_id == team_id)
            if game_id:
                game = self.db.query(Game).filter(Game.id == game_id).first()
                if game:
                    takeaway_query = takeaway_query.filter(GameEvent.game_id == game.game_id)
        
        takeaways = takeaway_query.count()
        pdi_score += takeaways * 1.8  # Weight for takeaways
        
        return pdi_score

    def calculate_xg_delta_psm(self, player_id=None, team_id=None, game_id=None):
        """
        Calculate xGΔPSM: The increase in expected goals due to passes
        (Expected Goals Delta from Pass Shot Movement)
        
        Args:
            player_id: Filter by player ID
            team_id: Filter by team ID
            game_id: Filter by game ID
            
        Returns:
            xGΔPSM value (float)
        """
        # Query passes that led to shots
        query = self.db.query(Pass).filter(Pass.completed == True)
        
        # Add filters
        if player_id:
            query = query.filter(Pass.passer_id == player_id)
        
        if team_id or game_id:
            query = query.join(GameEvent, Pass.event_id == GameEvent.id)
            if team_id:
                query = query.filter(GameEvent.team_id == team_id)
            if game_id:
                game = self.db.query(Game).filter(Game.id == game_id).first()
                if game:
                    query = query.filter(GameEvent.game_id == game.game_id)
        
        passes = query.all()
        
        total_xg_delta = 0.0
        
        for pass_event in passes:
            # Find shot that followed this pass within 3 seconds
            pass_game_event = self.db.query(GameEvent).filter(GameEvent.id == pass_event.event_id).first()
            if not pass_game_event:
                continue
                
            # Find shots that followed this pass
            shots_query = self.db.query(ShotEvent).join(
                GameEvent, ShotEvent.event_id == GameEvent.id
            ).filter(
                GameEvent.game_id == pass_game_event.game_id,
                GameEvent.period == pass_game_event.period,
                GameEvent.time_elapsed > pass_game_event.time_elapsed,
                GameEvent.time_elapsed <= pass_game_event.time_elapsed + 3.0  # Within 3 seconds
            )
            
            if pass_event.recipient_id:
                # If we know who received the pass, check if they took the shot
                shots_query = shots_query.filter(ShotEvent.shooter_id == pass_event.recipient_id)
            
            # Get the shots
            shots = shots_query.order_by(GameEvent.time_elapsed).all()
            
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
        """
        Detect the team's forecheck style based on recovery patterns.
        
        Args:
            team_id: Team ID to analyze
            game_id: Game ID to analyze
            
        Returns:
            Forecheck style: "AGGRESSIVE", "STANDARD", or "PASSIVE"
        """
        # Get offensive zone recoveries
        oz_recoveries = self.db.query(PuckRecovery).join(GameEvent).filter(
            GameEvent.game_id == game_id,
            GameEvent.team_id == team_id,
            PuckRecovery.zone == "OZ"
        ).all()
        
        # Get neutral zone recoveries
        nz_recoveries = self.db.query(PuckRecovery).join(GameEvent).filter(
            GameEvent.game_id == game_id,
            GameEvent.team_id == team_id,
            PuckRecovery.zone == "NZ"
        ).all()
        
        # Get all recoveries
        all_recoveries = len(oz_recoveries) + len(nz_recoveries)
        if all_recoveries == 0:
            return "STANDARD"  # Default if no data available
        
        # Calculate offensive zone recovery percentage
        oz_recovery_percentage = len(oz_recoveries) / all_recoveries if all_recoveries > 0 else 0
        
        # Get the percentage of recoveries that are forechecks
        forecheck_recoveries = sum(1 for recovery in oz_recoveries if recovery.recovery_type == "forecheck")
        forecheck_percentage = forecheck_recoveries / len(oz_recoveries) if len(oz_recoveries) > 0 else 0
        
        # Calculate the average depth of OZ recoveries (lower x_coordinate = deeper)
        if oz_recoveries:
            oz_events = [self.db.query(GameEvent).get(recovery.event_id) for recovery in oz_recoveries]
            oz_events = [e for e in oz_events if e is not None and e.x_coordinate is not None]
            avg_recovery_depth = sum(e.x_coordinate for e in oz_events) / len(oz_events) if oz_events else 0
        else:
            avg_recovery_depth = 0
        
        # Combine metrics to determine style
        # Aggressive: High OZ recovery %, high forecheck %, deeper average recovery
        # Passive: Low OZ recovery %, low forecheck %, less deep average recovery
        if oz_recovery_percentage > 0.7 and forecheck_percentage > 0.6 and avg_recovery_depth < 35:
            return "AGGRESSIVE"  # 2-1-2 or 2-3 forecheck
        elif oz_recovery_percentage < 0.3 or forecheck_percentage < 0.3 or avg_recovery_depth > 60:
            return "PASSIVE"  # 1-2-2 or 1-4 forecheck
        else:
            return "STANDARD"  # 1-2-2 with pressure or mixed approach

    def _detect_defensive_structure(self, team_id: int, game_id: str) -> str:
        """
        Detect the team's defensive structure based on defensive event patterns.
        
        Args:
            team_id: Team ID to analyze
            game_id: Game ID to analyze
            
        Returns:
            Defensive structure: "MAN_ON_MAN", "ZONE", "HYBRID", "COLLAPSE", or "AGGRESSIVE"
        """
        # Get game to determine which team is the opponent
        game = self.db.query(Game).filter(Game.game_id == game_id).first()
        if not game:
            return "ZONE"  # Default if game not found
        
        # Determine opponent team
        opponent_team_id = game.away_team_id if game.home_team_id == team_id else game.home_team_id
        
        # Get defensive events (blocks, hits, takeaways in defensive zone)
        defensive_events = self.db.query(GameEvent).filter(
            GameEvent.game_id == game_id,
            GameEvent.team_id == team_id,
            GameEvent.event_type.in_(["block", "hit", "takeaway"]),
            GameEvent.x_coordinate < -25  # Defensive zone
        ).all()
        
        # Get opponent's shots against
        opponent_shots = self.db.query(ShotEvent).join(GameEvent).filter(
            GameEvent.game_id == game_id,
            GameEvent.team_id == opponent_team_id
        ).all()
        
        # Get blocked shots
        blocks = [e for e in defensive_events if e.event_type == "block"]
        
        # Calculate metrics to determine structure
        if not defensive_events or not opponent_shots:
            return "ZONE"  # Default if no data available
        
        # 1. Calculate average distance between defensive players and shots
        # This requires player tracking data, which we don't have in this implementation
        # So we'll estimate based on available metrics
        
        # 2. Calculate block percentage - high block % suggests zone defense or collapse
        block_percentage = len(blocks) / len(opponent_shots) if opponent_shots else 0
        
        # 3. Analyze shot locations - clustering suggests zone or collapse
        # Get shot coordinates for opponent
        shot_coords = [(e.x_coordinate, e.y_coordinate) for e in opponent_shots 
                    if e.event is not None and e.event.x_coordinate is not None and e.event.y_coordinate is not None]
        
        # Calculate standard deviation of shot locations as a measure of dispersion
        # Low dispersion suggests opponent shooting from limited areas (zone defense)
        # High dispersion suggests opponent can shoot from anywhere (man-on-man with breakdowns)
        shot_x_coords = [x for x, y in shot_coords]
        shot_y_coords = [y for x, y in shot_coords]
        shot_x_dispersion = self._calculate_standard_deviation(shot_x_coords) if shot_x_coords else 0
        shot_y_dispersion = self._calculate_standard_deviation(shot_y_coords) if shot_y_coords else 0
        
        # 4. Check for high-danger shot prevention
        # Count shots from high-danger areas (slot)
        high_danger_shots = sum(1 for x, y in shot_coords if 
                            x > 60 and x < 85 and  # Near the net
                            y > 35 and y < 55)     # Middle of ice
        high_danger_percentage = high_danger_shots / len(shot_coords) if shot_coords else 0
        
        # Make determination based on metrics
        if block_percentage > 0.4 and high_danger_percentage < 0.2:
            return "COLLAPSE"  # Shot blocking and protecting slot
        elif shot_x_dispersion < 15 and shot_y_dispersion < 15:
            return "ZONE"  # Structured defense limiting shot locations
        elif high_danger_percentage < 0.15:
            return "HYBRID"  # Good slot protection but varied approach
        elif block_percentage < 0.2 and shot_x_dispersion > 25:
            return "AGGRESSIVE"  # Aggressive pressure but possibly allowing more shots
        else:
            return "MAN_ON_MAN"  # Default for other patterns

    def _detect_pp_formation(self, team_id: int, game_id: str) -> str:
        """
        Detect the power play formation for a team.
        
        Args:
            team_id: Team ID to analyze
            game_id: Game ID to analyze
            
        Returns:
            Power play formation: "1-3-1", "UMBRELLA", "OVERLOAD", "SPREAD", "DIAMOND_PLUS_ONE"
        """
        # Get game to determine power play situations
        game = self.db.query(Game).filter(Game.game_id == game_id).first()
        if not game:
            return "1-3-1"  # Default if game not found
        
        # Get power play events
        pp_events = self.db.query(GameEvent).filter(
            GameEvent.game_id == game_id,
            GameEvent.team_id == team_id,
            GameEvent.situation_code == "PP"  # Power play situations
        ).all()
        
        if not pp_events:
            return "1-3-1"  # Default if no power play events
        
        # Get passes during power play
        pp_passes = self.db.query(Pass).join(
            GameEvent, Pass.event_id == GameEvent.id
        ).filter(
            GameEvent.id.in_([e.id for e in pp_events]),
            Pass.completed == True
        ).all()
        
        # Get shots during power play
        pp_shots = self.db.query(ShotEvent).join(
            GameEvent, ShotEvent.event_id == GameEvent.id
        ).filter(
            GameEvent.id.in_([e.id for e in pp_events])
        ).all()
        
        # Analyze formation based on shot and pass locations
        # This is a simplification - a real implementation would use more sophisticated pattern recognition
        
        # Get shot coordinates
        shot_events = [self.db.query(GameEvent).get(shot.event_id) for shot in pp_shots]
        shot_coords = [(e.x_coordinate, e.y_coordinate) for e in shot_events 
                    if e is not None and e.x_coordinate is not None and e.y_coordinate is not None]
        
        # Count shots from different zones
        point_shots = sum(1 for x, y in shot_coords if x > 60)  # From the point
        wing_shots = sum(1 for x, y in shot_coords if x <= 60 and (y < 30 or y > 60))  # From the wings
        slot_shots = sum(1 for x, y in shot_coords if x <= 60 and y >= 30 and y <= 60)  # From the slot
        
        # Analyze pass patterns
        # For simplicity, we'll count zones where passes end
        pass_events = []
        for pp_pass in pp_passes:
            # We need both the origin and destination of passes
            pass_event = self.db.query(GameEvent).get(pp_pass.event_id)
            if not pass_event:
                continue
                
            # For destination, we'd ideally use the recipient's position
            # But for simplicity, we'll approximate based on available data
            if pp_pass.recipient_id:
                # Find an event by this recipient shortly after the pass
                recipient_event = self.db.query(GameEvent).filter(
                    GameEvent.game_id == game_id,
                    GameEvent.player_id == pp_pass.recipient_id,
                    GameEvent.time_elapsed > pass_event.time_elapsed,
                    GameEvent.time_elapsed <= pass_event.time_elapsed + 2  # Within 2 seconds
                ).order_by(GameEvent.time_elapsed).first()
                
                if recipient_event:
                    pass_events.append((pass_event, recipient_event))
        
        # Count pass patterns
        point_to_wing = sum(1 for src, dst in pass_events if 
                            src.x_coordinate > 60 and  # From point
                            (dst.y_coordinate < 30 or dst.y_coordinate > 60))  # To wing
        
        wing_to_wing = sum(1 for src, dst in pass_events if 
                        (src.y_coordinate < 30 or src.y_coordinate > 60) and  # From wing
                        (dst.y_coordinate < 30 or dst.y_coordinate > 60))  # To other wing
        
        wing_to_slot = sum(1 for src, dst in pass_events if 
                        (src.y_coordinate < 30 or src.y_coordinate > 60) and  # From wing
                        (dst.y_coordinate >= 30 and dst.y_coordinate <= 60))  # To slot
        
        point_to_slot = sum(1 for src, dst in pass_events if 
                            src.x_coordinate > 60 and  # From point
                            (dst.y_coordinate >= 30 and dst.y_coordinate <= 60))  # To slot
        
        # Make determination based on patterns
        if point_shots > wing_shots and point_to_slot > wing_to_slot:
            return "UMBRELLA"  # Heavy point presence with slot options
        elif wing_shots > point_shots and wing_to_slot > point_to_slot:
            return "OVERLOAD"  # Heavy wing presence
        elif wing_to_wing > point_to_wing and wing_to_wing > wing_to_slot:
            return "SPREAD"  # Spread formation with wing-to-wing movement
        elif slot_shots > wing_shots and slot_shots > point_shots:
            return "DIAMOND_PLUS_ONE"  # Diamond plus bumper in slot
        else:
            return "1-3-1"  # Default to 1-3-1, the most common formation

    def _detect_pk_formation(self, team_id: int, game_id: str) -> str:
        """
        Detect the penalty kill formation for a team.
        
        Args:
            team_id: Team ID to analyze
            game_id: Game ID to analyze
            
        Returns:
            Penalty kill formation: "DIAMOND", "BOX", "WEDGE_PLUS_ONE", "PASSIVE_TRIANGLE"
        """
        # Get game to determine penalty kill situations
        game = self.db.query(Game).filter(Game.game_id == game_id).first()
        if not game:
            return "BOX"  # Default if game not found
        
        # Get penalty kill events
        pk_events = self.db.query(GameEvent).filter(
            GameEvent.game_id == game_id,
            GameEvent.team_id == team_id,
            GameEvent.situation_code == "SH"  # Short-handed situations
        ).all()
        
        if not pk_events:
            return "BOX"  # Default if no penalty kill events
        
        # Determine opponent team
        opponent_team_id = game.away_team_id if game.home_team_id == team_id else game.home_team_id
        
        # Get opponent's shots during power play (team's penalty kill)
        pp_shots = self.db.query(ShotEvent).join(
            GameEvent, ShotEvent.event_id == GameEvent.id
        ).filter(
            GameEvent.game_id == game_id,
            GameEvent.team_id == opponent_team_id,
            GameEvent.situation_code == "PP"  # Power play
        ).all()
        
        # Get shot coordinates
        shot_events = [self.db.query(GameEvent).get(shot.event_id) for shot in pp_shots]
        shot_coords = [(e.x_coordinate, e.y_coordinate) for e in shot_events 
                    if e is not None and e.x_coordinate is not None and e.y_coordinate is not None]
        
        # Count shots from different zones
        point_shots = sum(1 for x, y in shot_coords if x > 60)  # From the point
        wing_shots = sum(1 for x, y in shot_coords if x <= 60 and (y < 30 or y > 60))  # From the wings
        slot_shots = sum(1 for x, y in shot_coords if x <= 60 and y >= 30 and y <= 60)  # From the slot
        
        # Get blocks and positioning during PK
        pk_blocks = [e for e in pk_events if e.event_type == "block"]
        
        block_coords = [(e.x_coordinate, e.y_coordinate) for e in pk_blocks
                    if e.x_coordinate is not None and e.y_coordinate is not None]
        
        # Count blocks by zone
        point_blocks = sum(1 for x, y in block_coords if x > 60)  # Blocks at the point
        wing_blocks = sum(1 for x, y in block_coords if x <= 60 and (y < 30 or y > 60))  # Blocks on wings
        slot_blocks = sum(1 for x, y in block_coords if x <= 60 and y >= 30 and y <= 60)  # Blocks in slot
        
        # Get takeaways during PK
        pk_takeaways = [e for e in pk_events if e.event_type == "takeaway"]
        
        # Calculate shot suppression metrics
        total_shots = len(shot_coords)
        if total_shots == 0:
            return "BOX"  # Default if no data available
        
        point_shot_percentage = point_shots / total_shots
        wing_shot_percentage = wing_shots / total_shots
        slot_shot_percentage = slot_shots / total_shots
        
        # Make determination based on patterns
        if slot_shot_percentage < 0.15 and slot_blocks > point_blocks:
            return "DIAMOND"  # Diamond protects slot well
        elif point_shot_percentage > 0.5 and len(pk_takeaways) < 2:
            return "BOX"  # Box allows point shots but protects the house
        elif wing_shot_percentage < 0.2 and len(pk_takeaways) > 3:
            return "WEDGE_PLUS_ONE"  # Wedge+1 applies pressure and takes away wings
        else:
            return "PASSIVE_TRIANGLE"  # Default for other patterns

    def _calculate_standard_deviation(self, values):
        """
        Calculate standard deviation of a list of values.
        
        Args:
            values: List of numeric values
            
        Returns:
            Standard deviation (float)
        """
        if not values or len(values) < 2:
            return 0.0
            
        n = len(values)
        mean = sum(values) / n
        variance = sum((x - mean) ** 2 for x in values) / n
        return variance ** 0.5