import logging
import math
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session

from app.models.base import Team, Player, GameEvent
from app.models.analytics import Game
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
        period_descriptor = play_data.get("periodDescriptor", {})
        period = period_descriptor.get("number")
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
        if event_type == "GOAL" or event_type == "SHOT" or event_type == "SHOT-ON-GOAL" or event_type == "MISSED-SHOT" or event_type == "BLOCKED-SHOT":
            self._process_shot_event(game_event, play_data)
        elif event_type == "FACEOFF":
            self._process_faceoff(game_event, play_data)
        elif event_type == "HIT":
            self._process_hit(game_event, play_data)
        elif event_type == "PENALTY":
            self._process_penalty(game_event, play_data)
        elif event_type == "TAKEAWAY" or event_type == "GIVEAWAY":
            self._process_turnover(game_event, play_data)
        elif event_type == "ZONE-ENTRY":
            self._detect_zone_entry(game_event, play_data)
        elif event_type == "PASS":
            self._process_pass(game_event, play_data)
        
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
        
        # Get shot type from either details.shotType or details.typeCode
        shot_type = details.get("shotType") or details.get("typeCode")
        
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
        
        # Determine if shot is a scoring chance, rush shot, or rebound shot
        is_scoring_chance = self._is_scoring_chance(distance, angle)
        is_high_danger = self._is_high_danger(distance, angle)
        rush_shot = self._is_rush_shot(play_data)
        rebound_shot = self._is_rebound_shot(play_data)
        
        # Get preceding event for context
        preceding_event_id = self._get_preceding_event_id(event, 10)  # Look at events within 10 seconds
        
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
            preceding_event_id=preceding_event_id,
            is_scoring_chance=is_scoring_chance,
            is_high_danger=is_high_danger,
            rush_shot=rush_shot,
            rebound_shot=rebound_shot
        )
        
        # Calculate xG based on NHL API documentation
        shot_event.xg = self._calculate_xg(shot_event, event)
        
        self.db.add(shot_event)
        self.db.commit()
        self.db.refresh(shot_event)
        return shot_event
    
    def _calculate_xg(self, shot_event: ShotEvent, event: GameEvent) -> float:
        """Calculate expected goals value based on shot data."""
        if shot_event.distance is None or shot_event.angle is None:
            return 0.05  # Default xG if no distance/angle
        
        # Simple formula: base xG decreases with distance, modified by angle
        # Will be replaced with a proper xG model in production
        xg_base = max(0.01, 1.0 - (shot_event.distance / 100))
        angle_factor = shot_event.angle / 90.0  # Normalize to 0-1
        xg = xg_base * (1.0 - (angle_factor * 0.7))
        
        # Adjust for shot type
        if shot_event.shot_type in ["Slap Shot", "SLAP_SHOT"]:
            xg *= 0.8
        elif shot_event.shot_type in ["Wrist Shot", "WRIST_SHOT"]:
            xg *= 1.1
        elif shot_event.shot_type in ["Deflected", "DEFLECTION"]:
            xg *= 1.3
        elif shot_event.shot_type in ["Snap Shot", "SNAP_SHOT"]:
            xg *= 1.0
        elif shot_event.shot_type in ["Backhand", "BACKHAND"]:
            xg *= 0.9
        elif shot_event.shot_type in ["Tip-In", "TIP_IN"]:
            xg *= 1.4

        # Adjust for rush and rebound
        if shot_event.rush_shot:
            xg *= 1.2
        if shot_event.rebound_shot:
            xg *= 1.3
            
        # Situational adjustments based on NHL API documentation
        if event.situation_code == "PP":  # Power play
            xg *= 1.2
        elif event.situation_code == "SH":  # Short-handed
            xg *= 0.7
            
        return min(0.95, xg)  # Cap at 0.95 probability
    
    def _get_preceding_event_id(self, event: GameEvent, time_window: float) -> Optional[int]:
        """Get the preceding event within a time window."""
        preceding_events = self.db.query(GameEvent).filter(
            GameEvent.game_id == event.game_id,
            GameEvent.period == event.period,
            GameEvent.time_elapsed < event.time_elapsed,
            GameEvent.time_elapsed >= (event.time_elapsed - time_window)
        ).order_by(GameEvent.time_elapsed.desc()).first()
        
        return preceding_events.id if preceding_events else None
    
    def _process_faceoff(self, event: GameEvent, play_data: Dict[str, Any]) -> None:
        """Process faceoff event."""
        details = play_data.get("details", {})
        winning_player_id_nhl = details.get("winningPlayerId")
        losing_player_id_nhl = details.get("losingPlayerId")
        
        winning_player_id = None
        losing_player_id = None
        
        # Get internal IDs for the players
        if winning_player_id_nhl:
            winning_player = self.db.query(Player).filter(Player.player_id == str(winning_player_id_nhl)).first()
            if winning_player:
                winning_player_id = winning_player.id
        
        if losing_player_id_nhl:
            losing_player = self.db.query(Player).filter(Player.player_id == str(losing_player_id_nhl)).first()
            if losing_player:
                losing_player_id = losing_player.id
        
        # Additional faceoff processing could be added here
        # For example, update player game stats for faceoff win/loss
        if winning_player_id:
            self._update_player_faceoff_stats(event.game_id, winning_player_id, True)
        
        if losing_player_id:
            self._update_player_faceoff_stats(event.game_id, losing_player_id, False)
    
    def _update_player_faceoff_stats(self, game_id: str, player_id: int, is_win: bool) -> None:
        """Update player's faceoff stats."""
        from app.models.analytics import Game, PlayerGameStats
        
        # Get the game's internal ID
        game = self.db.query(Game).filter(Game.game_id == game_id).first()
        if not game:
            return
        
        # Get or create player game stats
        stats = self.db.query(PlayerGameStats).filter(
            PlayerGameStats.game_id == game.id,
            PlayerGameStats.player_id == player_id
        ).first()
        
        if not stats:
            # Get player's team
            player = self.db.query(Player).filter(Player.id == player_id).first()
            if not player or not player.team_id:
                return
                
            stats = PlayerGameStats(
                player_id=player_id,
                game_id=game.id,
                team_id=player.team_id
            )
            self.db.add(stats)
        
        # Update faceoff stats
        stats.faceoffs_taken = (stats.faceoffs_taken or 0) + 1
        if is_win:
            stats.faceoffs_won = (stats.faceoffs_won or 0) + 1
        
        # Calculate percentage
        if stats.faceoffs_taken > 0:
            stats.faceoff_pct = (stats.faceoffs_won / stats.faceoffs_taken) * 100
        
        self.db.commit()
    
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
                    self._update_player_hit_stats(event.game_id, hitter_id)
            
            # Get hittee player
            hittee_nhl_id = hittee_data.get("playerId")
            if hittee_nhl_id:
                hittee = self.db.query(Player).filter(Player.player_id == str(hittee_nhl_id)).first()
                if hittee:
                    hittee_id = hittee.id
    
    def _update_player_hit_stats(self, game_id: str, player_id: int) -> None:
        """Update player's hit stats."""
        from app.models.analytics import Game, PlayerGameStats
        
        # Get the game's internal ID
        game = self.db.query(Game).filter(Game.game_id == game_id).first()
        if not game:
            return
        
        # Get or create player game stats
        stats = self.db.query(PlayerGameStats).filter(
            PlayerGameStats.game_id == game.id,
            PlayerGameStats.player_id == player_id
        ).first()
        
        if not stats:
            # Get player's team
            player = self.db.query(Player).filter(Player.id == player_id).first()
            if not player or not player.team_id:
                return
                
            stats = PlayerGameStats(
                player_id=player_id,
                game_id=game.id,
                team_id=player.team_id
            )
            self.db.add(stats)
        
        # Update hit stats
        stats.hits = (stats.hits or 0) + 1
        self.db.commit()
    
    def _process_turnover(self, event: GameEvent, play_data: Dict[str, Any]) -> None:
        """Process turnover event (takeaway/giveaway)."""
        participants = play_data.get("participants", [])
        
        if not participants:
            return
            
        player_data = participants[0]
        player_nhl_id = player_data.get("playerId")
        
        if not player_nhl_id:
            return
            
        player = self.db.query(Player).filter(Player.player_id == str(player_nhl_id)).first()
        if not player:
            return
            
        # Determine the zone where recovery happened
        zone = self._determine_zone(event.x_coordinate)
        
        # For takeaways, create puck recovery event
        if event.event_type == "TAKEAWAY":
            self.process_recovery(
                event,
                zone=zone,
                recovery_type="takeaway",
                player_id=player.id,
                lead_to_possession=True
            )
        
        # Processing could be expanded to track giveaways in player stats
    
    def _process_penalty(self, event: GameEvent, play_data: Dict[str, Any]) -> None:
        """Process penalty event."""
        details = play_data.get("details", {})
        penalty_type = details.get("typeCode") or details.get("penaltyTypeCode") or details.get("descKey")
        penalty_minutes = details.get("duration") or details.get("penaltyMinutes")
        
        # Get player who took the penalty
        participants = play_data.get("participants", [])
        if not participants:
            return
            
        player_data = participants[0]
        player_nhl_id = player_data.get("playerId")
        
        if not player_nhl_id:
            return
            
        player = self.db.query(Player).filter(Player.player_id == str(player_nhl_id)).first()
        if not player:
            return
            
        # Update player penalty minutes
        self._update_player_penalty_stats(event.game_id, player.id, penalty_minutes)
        
        # Additional penalty processing could be added here
        # For example, track power plays and penalty kills
        # For team on power play
        if event.team_id:
            opposing_team = self._get_opposing_team(event.game_id, event.team_id)
            if opposing_team:
                self._create_power_play_record(event, opposing_team.id, penalty_minutes)
    
    def _update_player_penalty_stats(self, game_id: str, player_id: int, penalty_minutes: int) -> None:
        """Update player's penalty stats."""
        from app.models.analytics import Game, PlayerGameStats
        
        # Ensure penalty_minutes is a number
        if not penalty_minutes:
            penalty_minutes = 2  # Default to a minor penalty
        else:
            try:
                penalty_minutes = int(penalty_minutes)
            except (ValueError, TypeError):
                penalty_minutes = 2
        
        # Get the game's internal ID
        game = self.db.query(Game).filter(Game.game_id == game_id).first()
        if not game:
            return
        
        # Get or create player game stats
        stats = self.db.query(PlayerGameStats).filter(
            PlayerGameStats.game_id == game.id,
            PlayerGameStats.player_id == player_id
        ).first()
        
        if not stats:
            # Get player's team
            player = self.db.query(Player).filter(Player.id == player_id).first()
            if not player or not player.team_id:
                return
                
            stats = PlayerGameStats(
                player_id=player_id,
                game_id=game.id,
                team_id=player.team_id
            )
            self.db.add(stats)
        
        # Update penalty stats
        stats.pim = (stats.pim or 0) + penalty_minutes
        self.db.commit()
    
    def _get_opposing_team(self, game_id: str, team_id: int) -> Optional[Team]:
        """Get the opposing team in a game."""
        game = self.db.query(Game).filter(Game.game_id == game_id).first()
        if not game:
            return None
            
        if game.home_team_id == team_id:
            return self.db.query(Team).filter(Team.id == game.away_team_id).first()
        else:
            return self.db.query(Team).filter(Team.id == game.home_team_id).first()
    
    def _create_power_play_record(self, event: GameEvent, team_id: int, penalty_minutes: int) -> None:
        """Create a power play record for the team that received the advantage."""
        from app.models.analytics import Game, PowerPlay
        
        # Get the game's internal ID
        game = self.db.query(Game).filter(Game.game_id == event.game_id).first()
        if not game:
            return
        
        # Convert penalty minutes to seconds
        if not penalty_minutes:
            duration = 120  # Default to 2 minutes
        else:
            try:
                duration = int(penalty_minutes) * 60
            except (ValueError, TypeError):
                duration = 120
        
        # Create power play record
        power_play = PowerPlay(
            game_id=game.id,
            team_id=team_id,
            start_time=event.time_elapsed,
            end_time=event.time_elapsed + duration,
            period=event.period,
            duration=duration,
            advantage_type="5v4",  # Default, would need more context to determine exact type
            successful=False  # Will be updated after power play is over
        )
        
        self.db.add(power_play)
        self.db.commit()
    
    def _detect_zone_entry(self, event: GameEvent, play_data: Dict[str, Any]) -> None:
        """Detect and process zone entry events."""
        # Zone entries often need to be inferred from consecutive events
        # This example shows how we might detect entry from a play sequence
        
        # Check if this is clearly a zone entry (in some APIs this may be explicit)
        if event.event_type == "ZONE-ENTRY" or "entry" in play_data.get("typeDescKey", "").lower():
            entry_type = self._determine_entry_type(event, play_data)
            controlled = entry_type != "dump"
            self.process_zone_entry(event, entry_type, controlled)
            return
            
        # If not explicitly labeled, try to infer from event sequence
        # This would require looking at previous events and coordinates
        # For example, if previous event was in neutral zone and this one is in offensive zone
        
        # This is a simplified example of inference - production code would be more sophisticated
        if event.event_type in ["SHOT", "SHOT-ON-GOAL", "GOAL"] and event.x_coordinate is not None:
            # Check if there was a recent event in the neutral zone
            previous_event = self._get_previous_event_in_zone(event, "NZ", 5)  # Within 5 seconds
            if previous_event:
                # This might be a zone entry leading to a shot
                entry_type = "carry"  # Default, could be refined with more analysis
                controlled = True
                zone_entry = self.process_zone_entry(previous_event, entry_type, controlled)
                
                # Mark that this entry led to a shot
                zone_entry.lead_to_shot = True
                zone_entry.lead_to_shot_time = event.time_elapsed - previous_event.time_elapsed
                self.db.commit()
    
    def _determine_entry_type(self, event: GameEvent, play_data: Dict[str, Any]) -> str:
        """Determine the type of zone entry."""
        details = play_data.get("details", {})
        if "carry" in str(details).lower():
            return "carry"
        elif "dump" in str(details).lower():
            return "dump"
        elif "pass" in str(details).lower():
            return "pass"
        
        # Default based on NHL API observation
        return "carry"
    
    def _get_previous_event_in_zone(self, event: GameEvent, zone: str, time_window: float) -> Optional[GameEvent]:
        """Get the previous event in a specific zone within a time window."""
        # Define zone boundaries based on NHL coordinates
        zone_filters = {
            "OZ": GameEvent.x_coordinate > 25,  # Offensive zone
            "NZ": (GameEvent.x_coordinate >= -25) & (GameEvent.x_coordinate <= 25),  # Neutral zone
            "DZ": GameEvent.x_coordinate < -25  # Defensive zone
        }
        
        if zone not in zone_filters:
            return None
            
        zone_filter = zone_filters[zone]
        
        previous_event = self.db.query(GameEvent).filter(
            GameEvent.game_id == event.game_id,
            GameEvent.period == event.period,
            GameEvent.time_elapsed < event.time_elapsed,
            GameEvent.time_elapsed >= (event.time_elapsed - time_window),
            zone_filter
        ).order_by(GameEvent.time_elapsed.desc()).first()
        
        return previous_event
    
    def _process_pass(self, event: GameEvent, play_data: Dict[str, Any]) -> None:
        """Process pass event."""
        participants = play_data.get("participants", [])
        
        if len(participants) < 2:
            return
            
        passer_data = participants[0]
        recipient_data = participants[1]
        
        # Get passer and recipient
        passer_nhl_id = passer_data.get("playerId")
        recipient_nhl_id = recipient_data.get("playerId")
        
        if not passer_nhl_id:
            return
            
        passer = self.db.query(Player).filter(Player.player_id == str(passer_nhl_id)).first()
        if not passer:
            return
            
        recipient = None
        if recipient_nhl_id:
            recipient = self.db.query(Player).filter(Player.player_id == str(recipient_nhl_id)).first()
            
        # Determine the zone where the pass occurred
        zone = self._determine_zone(event.x_coordinate)
        
        # Determine pass type based on NHL API data
        details = play_data.get("details", {})
        pass_type = details.get("passType", "direct")  # Default to "direct" if not specified
        
        # Determine if pass was completed
        completed = True  # Default to completed
        if "completed" in details:
            completed = details["completed"]
        elif not recipient:
            completed = False
            
        # Create pass event
        recipient_id = recipient.id if recipient else None
        self.process_pass(
            event,
            pass_type=pass_type,
            zone=zone,
            passer_id=passer.id,
            recipient_id=recipient_id,
            completed=completed
        )
        
        # Process potential shot assists (passes that lead to shots)
        if completed:
            self._check_and_record_shot_assist(event, passer.id, recipient_id)
            
    def _check_and_record_shot_assist(self, event: GameEvent, passer_id: int, recipient_id: Optional[int]) -> None:
        """Check if a pass led to a shot within a time window and record as potential assist."""
        # Only check for recipient shots if we have a recipient
        if not recipient_id:
            return
            
        # Look for shots by the recipient within 7 seconds (typical shot window)
        subsequent_shot = self.db.query(GameEvent).join(
            ShotEvent, ShotEvent.event_id == GameEvent.id
        ).filter(
            GameEvent.game_id == event.game_id,
            GameEvent.period == event.period,
            GameEvent.time_elapsed > event.time_elapsed,
            GameEvent.time_elapsed <= event.time_elapsed + 7,  # 7-second window
            ShotEvent.shooter_id == recipient_id
        ).order_by(GameEvent.time_elapsed).first()
        
        if subsequent_shot:
            # Update the shot event to record this pass as potentially leading to the shot
            shot = self.db.query(ShotEvent).filter(ShotEvent.event_id == subsequent_shot.id).first()
            if shot:
                # Record xG delta if appropriate
                self._calculate_and_record_xg_delta(event, shot, passer_id)
                
                # If it's a goal and doesn't have assists yet, consider this as potential assist
                if shot.goal and not shot.primary_assist_id:
                    shot.primary_assist_id = passer_id
                    self.db.commit()
    
    def _calculate_and_record_xg_delta(self, pass_event: GameEvent, shot_event: ShotEvent, passer_id: int) -> None:
        """Calculate how the pass improved xG compared to a shot from the pass location."""
        # This is a simplified implementation
        # A full implementation would consider more factors
        
        from app.models.analytics import PlayerGameStats, Game
        
        # Calculate xG if shot had been taken from the pass location
        pass_location_xg = 0.0
        if pass_event.x_coordinate is not None and pass_event.y_coordinate is not None:
            # Simple calculation based on distance and angle
            goal_x = 89
            goal_y = 0
            
            # Calculate distance in feet
            distance = math.sqrt((pass_event.x_coordinate - goal_x) ** 2 + (pass_event.y_coordinate - goal_y) ** 2)
            
            # Calculate angle (0 is straight on, 90 is from side)
            angle = 0
            if pass_event.x_coordinate != goal_x:  # Avoid division by zero
                angle = math.degrees(math.atan(abs(pass_event.y_coordinate - goal_y) / abs(pass_event.x_coordinate - goal_x)))
            
            # Simple xG model
            xg_base = max(0.01, 1.0 - (distance / 100))
            angle_factor = angle / 90.0  # Normalize to 0-1
            pass_location_xg = xg_base * (1.0 - (angle_factor * 0.7))
        
        # Calculate xG delta (improvement due to pass)
        actual_xg = shot_event.xg or 0.0
        xg_delta = max(0, actual_xg - pass_location_xg)  # Never negative
        
        # Record this for the passing player's stats
        # Get the game's internal ID
        game = self.db.query(Game).filter(Game.game_id == pass_event.game_id).first()
        if not game:
            return
        
        # Get or create player game stats
        stats = self.db.query(PlayerGameStats).filter(
            PlayerGameStats.game_id == game.id,
            PlayerGameStats.player_id == passer_id
        ).first()
        
        if not stats:
            # Get player's team
            player = self.db.query(Player).filter(Player.id == passer_id).first()
            if not player or not player.team_id:
                return
                
            stats = PlayerGameStats(
                player_id=passer_id,
                game_id=game.id,
                team_id=player.team_id
            )
            self.db.add(stats)
        
        # Update xGΔPSM (xG delta from Pass Shot Movement)
        stats.xg_delta_psm = (stats.xg_delta_psm or 0.0) + xg_delta
        self.db.commit()
    
    def _determine_zone(self, x_coordinate: Optional[float]) -> str:
        """Determine the zone based on x coordinate."""
        if x_coordinate is None:
            return "NZ"  # Default to neutral zone if unknown
            
        if x_coordinate > 25:
            return "OZ"  # Offensive zone
        elif x_coordinate < -25:
            return "DZ"  # Defensive zone
        else:
            return "NZ"  # Neutral zone
    
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
        # Determine if this was a rush entry
        attack_speed = "RUSH" if self._is_rush_entry(event) else "CONTROLLED"
        
        zone_entry = ZoneEntry(
            event_id=event.id,
            entry_type=entry_type,
            controlled=controlled,
            player_id=player_id or event.player_id,
            defender_id=defender_id,
            lead_to_shot=False,  # Will be updated if a shot follows
            attack_speed=attack_speed
        )
        self.db.add(zone_entry)
        self.db.commit()
        self.db.refresh(zone_entry)
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
        # Calculate distance and angle change if coordinates are available
        distance = None
        angle_change = None
        
        # Would need additional context for full implementation
        
        pass_event = Pass(
            event_id=event.id,
            passer_id=passer_id or event.player_id,
            recipient_id=recipient_id,
            pass_type=pass_type,
            zone=zone,
            completed=completed,
            distance=distance,
            angle_change=angle_change
        )
        self.db.add(pass_event)
        self.db.commit()
        self.db.refresh(pass_event)
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
        # Look for event that preceded this recovery
        preceded_by_id = self._get_preceding_event_id(event, 5)  # 5-second window
        
        recovery = PuckRecovery(
            event_id=event.id,
            player_id=player_id or event.player_id,
            zone=zone,
            recovery_type=recovery_type,
            lead_to_possession=lead_to_possession,
            preceded_by_id=preceded_by_id
        )
        self.db.add(recovery)
        self.db.commit()
        self.db.refresh(recovery)
        
        # Update player's Puck Recovery Impact (PRI) metric
        self._update_player_pri(event.game_id, player_id or event.player_id, zone, recovery_type, lead_to_possession)
        
        return recovery
    
    def _update_player_pri(self, game_id: str, player_id: int, zone: str, recovery_type: str, lead_to_possession: bool) -> None:
        """Update player's Puck Recovery Impact (PRI) metric."""
        from app.models.analytics import Game, PlayerGameStats
        
        # Get the game's internal ID
        game = self.db.query(Game).filter(Game.game_id == game_id).first()
        if not game:
            return
        
        # Get or create player game stats
        stats = self.db.query(PlayerGameStats).filter(
            PlayerGameStats.game_id == game.id,
            PlayerGameStats.player_id == player_id
        ).first()
        
        if not stats:
            # Get player's team
            player = self.db.query(Player).filter(Player.id == player_id).first()
            if not player or not player.team_id:
                return
                
            stats = PlayerGameStats(
                player_id=player_id,
                game_id=game.id,
                team_id=player.team_id
            )
            self.db.add(stats)
        
        # Calculate PRI value for this recovery
        pri_value = 1.0  # Base value
        
        # Adjust based on zone
        if zone == "OZ":
            pri_value *= 2.0  # Offensive zone recoveries worth more
        elif zone == "DZ":
            pri_value *= 0.5  # Defensive zone recoveries worth less
        
        # Adjust based on recovery type
        if recovery_type == "forecheck":
            pri_value *= 1.5  # Forecheck recoveries worth more
        elif recovery_type == "takeaway":
            pri_value *= 2.0  # Takeaways worth most
        
        # Adjust based on outcome
        if lead_to_possession:
            pri_value *= 1.5  # Recoveries leading to possession worth more
        
        # Update PRI
        stats.pri = (stats.pri or 0.0) + pri_value
        self.db.commit()
    
    def _is_scoring_chance(self, distance: Optional[float], angle: Optional[float]) -> bool:
        """Determine if a shot is a scoring chance based on distance and angle."""
        if distance is None or angle is None:
            return False
        
        # Based on NHL API documentation - scoring chances are generally:
        # 1. Shots from high-danger areas (slot, close to net)
        # 2. Shots with low angle (more direct at goal)
        # 3. Shots within a specific distance
        
        # Simple scoring chance definition
        return distance < 25 or angle < 30
    
    def _is_high_danger(self, distance: Optional[float], angle: Optional[float]) -> bool:
        """Determine if a shot is from a high danger area based on distance and angle."""
        if distance is None or angle is None:
            return False
        
        # Based on NHL analytics - high danger areas are typically:
        # 1. Shots from very close to net (inner slot)
        # 2. Shots with very direct angle at goal
        
        # Simple high danger definition
        return distance < 15 or angle < 15
    
    def _is_rush_shot(self, play_data: Dict[str, Any]) -> bool:
        """Determine if a shot is a rush shot based on play data."""
        # This would typically require looking at preceding events
        # For example, if there was a zone entry within 5-7 seconds
        
        # For now, use a placeholder implementation
        details = play_data.get("details", {})
        return "rush" in str(details).lower() or "rusa" in str(details).lower()
    
    def _is_rebound_shot(self, play_data: Dict[str, Any]) -> bool:
        """Determine if a shot is a rebound shot based on play data."""
        # This would typically require looking at preceding events
        # For example, if there was another shot within 2-3 seconds
        
        # For now, use a placeholder implementation
        details = play_data.get("details", {})
        return "rebound" in str(details).lower()
    
    def _is_rush_entry(self, event: GameEvent) -> bool:
        """Determine if a zone entry is a rush based on event data."""
        # Rush entries typically involve higher speed through neutral zone
        # Would need to look at preceding events for full implementation
        
        # As a placeholder, check for rapid progression through zones
        preceding_events = self.db.query(GameEvent).filter(
            GameEvent.game_id == event.game_id,
            GameEvent.period == event.period,
            GameEvent.time_elapsed < event.time_elapsed,
            GameEvent.time_elapsed >= (event.time_elapsed - 5)  # 5-second window
        ).order_by(GameEvent.time_elapsed.desc()).all()
        
        if len(preceding_events) < 2:
            return False
        
        # Look for quick succession of events across zones
        zone_progression = []
        for prev_event in preceding_events:
            if prev_event.x_coordinate is not None:
                zone = self._determine_zone(prev_event.x_coordinate)
                zone_progression.append(zone)
        
        # Check for transitions through zones
        if len(zone_progression) >= 2:
            # If we see progression from defensive/neutral to offensive zone within a few seconds
            has_dz_or_nz = "DZ" in zone_progression or "NZ" in zone_progression
            current_zone = self._determine_zone(event.x_coordinate)
            return has_dz_or_nz and current_zone == "OZ"
        
        return False