# Create a new file: app/services/sequence_service.py
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.models.base import GameEvent
from app.models.analytics import Pass, ShotEvent, ZoneEntry

logger = logging.getLogger(__name__)

class SequenceService:
    def __init__(self, db: Session):
        self.db = db
    
    def detect_cycles(db, game_id, team_id):
        """
        Detect offensive zone cycling patterns
        """
        # Get consecutive passes in offensive zone
        passes = db.query(Pass).join(GameEvent).filter(
            GameEvent.game_id == game_id,
            GameEvent.team_id == team_id,
            Pass.zone == "OZ",
            Pass.completed == True
        ).order_by(GameEvent.period, GameEvent.time_elapsed).all()
        
        cycles = []
        current_cycle = []
        
        for i in range(len(passes) - 1):
            current_pass = passes[i]
            next_pass = passes[i + 1]
            
            # Get the events
            current_event = db.query(GameEvent).filter(GameEvent.id == current_pass.event_id).first()
            next_event = db.query(GameEvent).filter(GameEvent.id == next_pass.event_id).first()
            
            # Check if passes are within the same period
            if current_event.period != next_event.period:
                # End of cycle
                if len(current_cycle) >= 3:  # Consider it a cycle if 3+ consecutive passes
                    cycles.append(current_cycle)
                current_cycle = []
                continue
                
            # Check if passes are within 4 seconds of each other
            if next_event.time_elapsed - current_event.time_elapsed <= 4.0:
                if not current_cycle:  # Start new cycle
                    current_cycle.append(current_pass)
                current_cycle.append(next_pass)
            else:
                # Time gap too large, end of cycle
                if len(current_cycle) >= 3:
                    cycles.append(current_cycle)
                current_cycle = []
        
        # Add the last cycle if it exists
        if len(current_cycle) >= 3:
            cycles.append(current_cycle)
            
        return cycles
    
    def detect_rush_plays(db, game_id, team_id):
        """
        Detect rush plays (rapid progression through zones)
        """
        # Get consecutive events for the team
        events = db.query(GameEvent).filter(
            GameEvent.game_id == game_id,
            GameEvent.team_id == team_id
        ).order_by(GameEvent.period, GameEvent.time_elapsed).all()
        
        rush_plays = []
        
        for i in range(len(events) - 2):  # Need at least 3 events for a rush
            start_event = events[i]
            end_event = events[i + 2]  # Look 2 events ahead
            
            # Check if events are in the same period
            if start_event.period != end_event.period:
                continue
                
            # Check if progression happened within 5 seconds
            if end_event.time_elapsed - start_event.time_elapsed <= 5.0:
                # Check if there was zone progression (DZ -> NZ -> OZ)
                start_zone = determine_zone(start_event.x_coordinate)
                end_zone = determine_zone(end_event.x_coordinate)
                
                if (start_zone == "DZ" and end_zone == "OZ") or \
                (start_zone == "DZ" and end_zone == "NZ") or \
                (start_zone == "NZ" and end_zone == "OZ"):
                    # This is a rush play
                    rush_sequence = events[i:i+3]  # Include the 3 events
                    rush_plays.append(rush_sequence)
        
        return rush_plays
    
    def determine_zone(self, x_coordinate: Optional[float]) -> str:
        """
        Determine which zone a coordinate is in based on x position.
        
        Args:
            x_coordinate: X coordinate on the ice
            
        Returns:
            Zone code: "OZ" (offensive zone), "NZ" (neutral zone), or "DZ" (defensive zone)
        """
        if x_coordinate is None:
            return "NZ"  # Default to neutral zone if coordinates are missing
        
        # Using standard NHL coordinate system where:
        # - Center ice is around x=0
        # - Defensive zone is negative x values (team's own end)
        # - Offensive zone is positive x values (opponent's end)
        # - Blue lines are at approximately x=-25 and x=25
        
        if x_coordinate > 25:
            return "OZ"  # Offensive zone
        elif x_coordinate < -25:
            return "DZ"  # Defensive zone
        else:
            return "NZ"  # Neutral zone