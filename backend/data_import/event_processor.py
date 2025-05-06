import logging
import math
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session

from app.models.base import Game, Team, Player, GameEvent
from app.models.analytics import ShotEvent, ZoneEntry, Pass, PuckRecovery

logger = logging.getLogger(__name__)


class EventProcessor:
    """
    Processes raw NHL event data and converts it to PuckPattern's data model.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def process_event(self, game: Game, play_data: Dict[str, Any]) -> Optional[GameEvent]:
        """
        Process a play event from NHL API and create corresponding database entries.
        
        Args:
            game: Game object
            play_data: Play data from NHL API
            
        Returns:
            Created game event
        """
        # Extract basic event data
        event_type = play_data.get("typeDescKey")
        if not event_type:
            logger.warning(f"Missing event type in play data: {play_data}")
            return None
        
        # Get period and time
        period = play_data.get("period")
        time_in_period = play_data.get("timeInPeriod")
        time_remaining = play_data.get("timeRemaining")
        
        if not period or not time_in_period:
            logger.warning(f"Missing period info in play data: {play_data}")
            return None
        
        # Convert time to seconds
        time_parts = time_in_period.split(":")
        time_elapsed = int(time_parts[0]) * 60 + int(time_parts[1])
        
        # Get coordinates
        x_coordinate = play_data.get("xCoord")
        y_coordinate = play_data.get("yCoord")
        
        # Get team and player
        team_id = None
        player_id = None
        
        if "team" in play_data:
            team_abbrev = play_data["team"].get("abbrev")
            if team_abbrev:
                team = self.db.query(Team).filter(Team.abbreviation == team_abbrev).first()
                if team:
                    team_id = team.id
        
        # Get player from the first participant if available
        participants = play_data.get("participants", [])
        if participants and len(participants) > 0:
            player_data = participants[0]
            nhl_player_id = player_data.get("playerId")
            if nhl_player_id:
                player = self.db.query(Player).filter(Player.player_id == str(nhl_player_id)).first()
                if player:
                    player_id = player.id
        
        # Create base game event
        game_event = GameEvent(
            game_id=game.game_id,
            event_type=event_type,
            period=period,
            time_elapsed=time_elapsed,
            time_remaining=time_remaining,
            x_coordinate=x_coordinate,
            y_coordinate=y_coordinate,
            player_id=player_id,
            team_id=team_id,
            situation_code=play_data.get("situationCode"),
            is_scoring_play=play_data.get("isScoringPlay", False),
            is_penalty=play_data.get("isPenalty", False),
            sort_order=play_data.get("sortOrder"),
            event_id=play_data.get("eventId")
        )
        self.db.add(game_event)
        self.db.commit()
        self.db.refresh(game_event)
        
        # Process specific event types
        if event_type == "GOAL":
            self._process_shot_event(game_event, play_data)
        elif event_type == "SHOT" or event_type == "SHOT-ON-GOAL":
            self._process_shot_event(game_event, play_data)
        elif event_type == "MISSED-SHOT" or event_type == "BLOCKED-SHOT":
            self._process_shot_event(game_event, play_data)
        elif event_type == "FACEOFF":
            self._process_faceoff(game_event, play_data)
        elif event_type == "HIT":
            self._process_hit(game_event, play_data)
        elif event_type == "PENALTY":
            self._process_penalty(game_event, play_data)
        elif event_type == "TAKEAWAY" or event_type == "GIVEAWAY":
            self._process_turnover(game_event, play_data)
        # Add more event type processing as needed
        
        return game_event
    
    def _process_shot_event(self, event: GameEvent, play_data: Dict[str, Any]) -> Optional[ShotEvent]:
        """
        Process shot or goal event.
        
        Args:
            event: Base game event
            play_data: Play data from NHL API
            
        Returns:
            Created shot event
        """
        details = play_data.get("details", {})
        is_goal = (event.event_type == "GOAL")
        shot_type = details.get("shotType")
        
        # Default values
        distance = None
        angle = None
        
        # Calculate distance and angle if coordinates available
        if event.x_coordinate is not None and event.y_coordinate is not None:
            # NHL coordinates: center ice is 0,0, goal lines at +/-89 feet
            # Distance from goal line is x_coordinate +/- 89 (depending on side)
            # For simplicity assume shots are always toward the right goal
            goal_x = 89
            goal_y = 0
            
            # Calculate distance in feet
            distance = math.sqrt((event.x_coordinate - goal_x) ** 2 + (event.y_coordinate - goal_y) ** 2)
            
            # Calculate angle (0 is straight on, 90 is from side)
            if event.x_coordinate != goal_x:  # Avoid division by zero
                angle = math.degrees(math.atan(abs(event.y_coordinate - goal_y) / abs(event.x_coordinate - goal_x)))
        
        # Get shooter and goalie
        shooter_id = None
        goalie_id = None
        primary_assist_id = None
        secondary_assist_id = None
        
        # Process participants
        participants = play_data.get("participants", [])
        for participant in participants:
            nhl_player_id = participant.get("playerId")
            if not nhl_player_id:
                continue
            
            player = self.db.query(Player).filter(Player.player_id == str(nhl_player_id)).first()
            if not player:
                continue
            
            # Determine participant role
            if "shooterPlayerId" in details and str(nhl_player_id) == str(details["shooterPlayerId"]):
                shooter_id = player.id
            elif "scoringPlayerId" in details and str(nhl_player_id) == str(details["scoringPlayerId"]):
                shooter_id = player.id
            elif "goalieInNetId" in details and str(nhl_player_id) == str(details["goalieInNetId"]):
                goalie_id = player.id
            elif "assist1PlayerId" in details and str(nhl_player_id) == str(details["assist1PlayerId"]):
                primary_assist_id = player.id
            elif "assist2PlayerId" in details and str(nhl_player_id) == str(details["assist2PlayerId"]):
                secondary_assist_id = player.id
        
        # If no shooter identified, use the first player
        if shooter_id is None and participants:
            first_player_id = participants[0].get("playerId")
            if first_player_id:
                player = self.db.query(Player).filter(Player.player_id == str(first_player_id)).first()
                if player:
                    shooter_id = player.id
        
        # Create shot event
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
            is_scoring_chance=self._is_scoring_chance(distance, angle),
            is_high_danger=self._is_high_danger(distance, angle),
            rush_shot=self._is_rush_shot(play_data),
            rebound_shot=self._is_rebound_shot(play_data)
        )
        
        # Calculate simple xG based on distance and angle
        if distance and angle is not None:
            # Simple formula: base xG decreases with distance, modified by angle
            # Will be replaced with a proper xG model in production
            xg_base = max(0.01, 1.0 - (distance / 100))
            angle_factor = angle / 90.0  # Normalize to 0-1
            shot_event.xg = xg_base * (1.0 - (angle_factor * 0.7))
            
            # Adjust for shot type
            if shot_type == "Slap Shot" or shot_type == "SLAP_SHOT":
                shot_event.xg *= 0.8
            elif shot_type == "Wrist Shot" or shot_type == "WRIST_SHOT":
                shot_event.xg *= 1.1
            elif shot_type == "Deflected" or shot_type == "DEFLECTION":
                shot_event.xg *= 1.3
            elif shot_type == "Snap Shot" or shot_type == "SNAP_SHOT":
                shot_event.xg *= 1.0
            elif shot_type == "Backhand" or shot_type == "BACKHAND":
                shot_event.xg *= 0.9
            elif shot_type == "Tip-In" or shot_type == "TIP_IN":
                shot_event.xg *= 1.4

            # Adjust for rush and rebound
            if shot_event.rush_shot:
                shot_event.xg *= 1.2
            if shot_event.rebound_shot:
                shot_event.xg *= 1.3
        
        self.db.add(shot_event)
        self.db.commit()
        return shot_event
    
    def _process_faceoff(self, event: GameEvent, play_data: Dict[str, Any]) -> None:
        """Process faceoff event."""
        details = play_data.get("details", {})
        winning_player_id = details.get("winningPlayerId")
        losing_player_id = details.get("losingPlayerId")
        
        # Additional faceoff processing could be added here
        pass
    
    def _process_hit(self, event: GameEvent, play_data: Dict[str, Any]) -> None:
        """Process hit event."""
        participants = play_data.get("participants", [])
        
        hitter_id = None
        hittee_id = None
        
        # Extract hitter and hittee from participants
        if len(participants) >= 2:
            hitter_data = participants[0]
            hittee_data = participants[1]
            
            # Get hitter player
            hitter_nhl_id = hitter_data.get("playerId")
            if hitter_nhl_id:
                hitter = self.db.query(Player).filter(Player.player_id == str(hitter_nhl_id)).first()
                if hitter:
                    hitter_id = hitter.id
            
            # Get hittee player
            hittee_nhl_id = hittee_data.get("playerId")
            if hittee_nhl_id:
                hittee = self.db.query(Player).filter(Player.player_id == str(hittee_nhl_id)).first()
                if hittee:
                    hittee_id = hittee.id
        
        # Additional hit processing could be added here
        pass
    
    def _process_turnover(self, event: GameEvent, play_data: Dict[str, Any]) -> None:
        """Process turnover event (takeaway/giveaway)."""
        # Additional turnover processing could be added here
        pass
    
    def _process_penalty(self, event: GameEvent, play_data: Dict[str, Any]) -> None:
        """Process penalty event."""
        details = play_data.get("details", {})
        penalty_type = details.get("typeCode") or details.get("penaltyTypeCode")
        penalty_minutes = details.get("duration") or details.get("penaltyMinutes")
        
        # Additional penalty processing could be added here
        pass
    
    def process_zone_entry(self, event: GameEvent, entry_type: str, controlled: bool, player_id: Optional[int] = None, defender_id: Optional[int] = None) -> ZoneEntry:
        """
        Process zone entry event.
        
        Args:
            event: Base game event
            entry_type: Type of entry (carry, dump, pass)
            controlled: Whether entry was controlled
            player_id: Player making the entry
            defender_id: Defender involved
            
        Returns:
            Created zone entry
        """
        zone_entry = ZoneEntry(
            event_id=event.id,
            entry_type=entry_type,
            controlled=controlled,
            player_id=player_id or event.player_id,
            defender_id=defender_id,
            attack_speed="RUSH" if self._is_rush_entry(event) else "CONTROLLED"
        )
        self.db.add(zone_entry)
        self.db.commit()
        return zone_entry
    
    def process_pass(self, event: GameEvent, pass_type: str, zone: str, passer_id: Optional[int] = None, recipient_id: Optional[int] = None, completed: bool = True) -> Pass:
        """
        Process pass event.
        
        Args:
            event: Base game event
            pass_type: Type of pass
            zone: Zone where pass occurred
            passer_id: Player making the pass
            recipient_id: Player receiving the pass
            completed: Whether pass was completed
            
        Returns:
            Created pass event
        """
        pass_event = Pass(
            event_id=event.id,
            passer_id=passer_id or event.player_id,
            recipient_id=recipient_id,
            pass_type=pass_type,
            zone=zone,
            completed=completed
        )
        self.db.add(pass_event)
        self.db.commit()
        return pass_event
    
    def process_recovery(self, event: GameEvent, zone: str, recovery_type: str, player_id: Optional[int] = None, lead_to_possession: bool = True) -> PuckRecovery:
        """
        Process puck recovery event.
        
        Args:
            event: Base game event
            zone: Zone where recovery occurred
            recovery_type: Type of recovery
            player_id: Player making the recovery
            lead_to_possession: Whether recovery led to possession
            
        Returns:
            Created recovery event
        """
        recovery = PuckRecovery(
            event_id=event.id,
            player_id=player_id or event.player_id,
            zone=zone,
            recovery_type=recovery_type,
            lead_to_possession=lead_to_possession
        )
        self.db.add(recovery)
        self.db.commit()
        return recovery
    
    def _is_scoring_chance(self, distance: Optional[float], angle: Optional[float]) -> bool:
        """Determine if a shot is a scoring chance based on distance and angle."""
        if distance is None or angle is None:
            return False
        
        # Simple scoring chance definition
        # Shots from inside 25 feet or with angle less than 30 degrees
        return distance < 25 or angle < 30
    
    def _is_high_danger(self, distance: Optional[float], angle: Optional[float]) -> bool:
        """Determine if a shot is from a high danger area based on distance and angle."""
        if distance is None or angle is None:
            return False
        
        # Simple high danger definition
        # Shots from inside 15 feet or with angle less than 15 degrees
        return distance < 15 or angle < 15
    
    def _is_rush_shot(self, play_data: Dict[str, Any]) -> bool:
        """Determine if a shot is a rush shot based on play data."""
        # This would need to be implemented based on tracking preceding events
        # For now, return a simple placeholder implementation
        return False
    
    def _is_rebound_shot(self, play_data: Dict[str, Any]) -> bool:
        """Determine if a shot is a rebound shot based on play data."""
        # This would need to be implemented based on tracking preceding events
        # For now, return a simple placeholder implementation
        return False
    
    def _is_rush_entry(self, event: GameEvent) -> bool:
        """Determine if a zone entry is a rush based on event data."""
        # This would need to be implemented based on tracking preceding events
        # For now, return a simple placeholder implementation
        return False