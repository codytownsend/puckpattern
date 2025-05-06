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
        event_type = play_data.get("result", {}).get("eventTypeId")
        if not event_type:
            logger.warning(f"Missing event type in play data: {play_data}")
            return None
        
        # Get period and time
        period = play_data.get("about", {}).get("period")
        period_time = play_data.get("about", {}).get("periodTime")
        
        if not period or not period_time:
            logger.warning(f"Missing period info in play data: {play_data}")
            return None
        
        # Convert time to seconds
        time_parts = period_time.split(":")
        time_elapsed = int(time_parts[0]) * 60 + int(time_parts[1])
        
        # Get coordinates
        coordinates = play_data.get("coordinates", {})
        x_coordinate = coordinates.get("x")
        y_coordinate = coordinates.get("y")
        
        # Get team and player
        team_id = None
        player_id = None
        
        if "team" in play_data:
            nhl_team_id = play_data["team"].get("id")
            if nhl_team_id:
                team = self.db.query(Team).filter(Team.team_id == str(nhl_team_id)).first()
                if team:
                    team_id = team.id
        
        # Get player from the first player in players list if available
        players = play_data.get("players", [])
        if players and "player" in players[0]:
            nhl_player_id = players[0]["player"].get("id")
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
            x_coordinate=x_coordinate,
            y_coordinate=y_coordinate,
            player_id=player_id,
            team_id=team_id
        )
        self.db.add(game_event)
        self.db.commit()
        self.db.refresh(game_event)
        
        # Process specific event types
        if event_type == "SHOT" or event_type == "GOAL":
            self._process_shot_event(game_event, play_data)
        elif event_type == "FACEOFF":
            self._process_faceoff(game_event, play_data)
        elif event_type == "HIT":
            self._process_hit(game_event, play_data)
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
        result = play_data.get("result", {})
        event_type = result.get("eventTypeId")
        shot_type = result.get("secondaryType")
        
        # Default values
        is_goal = (event_type == "GOAL")
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
        
        players = play_data.get("players", [])
        for player_info in players:
            player_type = player_info.get("playerType")
            nhl_player_id = player_info.get("player", {}).get("id")
            
            if not nhl_player_id:
                continue
            
            player = self.db.query(Player).filter(Player.player_id == str(nhl_player_id)).first()
            if not player:
                continue
            
            if player_type == "Shooter" or player_type == "Scorer":
                shooter_id = player.id
            elif player_type == "Goalie":
                goalie_id = player.id
            elif player_type == "Assist" and primary_assist_id is None:
                primary_assist_id = player.id
            elif player_type == "Assist" and primary_assist_id is not None:
                secondary_assist_id = player.id
        
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
            secondary_assist_id=secondary_assist_id
        )
        
        # Calculate simple xG based on distance and angle
        if distance and angle is not None:
            # Simple formula: base xG decreases with distance, modified by angle
            # Will be replaced with a proper xG model in production
            xg_base = max(0.01, 1.0 - (distance / 100))
            angle_factor = angle / 90.0  # Normalize to 0-1
            shot_event.xg = xg_base * (1.0 - (angle_factor * 0.7))
            
            # Adjust for shot type
            if shot_type == "Slap Shot":
                shot_event.xg *= 0.8
            elif shot_type == "Wrist Shot":
                shot_event.xg *= 1.1
            elif shot_type == "Deflected":
                shot_event.xg *= 1.3
            elif shot_type == "Snap Shot":
                shot_event.xg *= 1.0
            elif shot_type == "Backhand":
                shot_event.xg *= 0.9
            elif shot_type == "Tip-In":
                shot_event.xg *= 1.4
        
        self.db.add(shot_event)
        self.db.commit()
        return shot_event
    
    def _process_faceoff(self, event: GameEvent, play_data: Dict[str, Any]) -> None:
        """Process faceoff event."""
        # This would create a specialized faceoff event record
        # For now we'll just use the base event
        pass
    
    def _process_hit(self, event: GameEvent, play_data: Dict[str, Any]) -> None:
        """Process hit event."""
        # This would create a specialized hit event record
        # For now we'll just use the base event
        pass
    
    def _process_turnover(self, event: GameEvent, play_data: Dict[str, Any]) -> None:
        """Process turnover event (takeaway/giveaway)."""
        # This would create a specialized turnover event record
        # For now we'll just use the base event
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
            defender_id=defender_id
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