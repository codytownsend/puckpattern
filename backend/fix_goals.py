# fix_player_shots.py
from app.db.session import SessionLocal
from app.models.base import Player, GameEvent
from app.models.analytics import ShotEvent, Game
from sqlalchemy import func

# Create session
db = SessionLocal()

try:
    # Check a specific player (Schwartz)
    player = db.query(Player).filter(Player.player_id == "8475768").first()
    if player:
        print(f"Found player: {player.name} (ID: {player.id})")
        
        # Look for shot events in game_events associated with this player
        player_shot_events = db.query(GameEvent).filter(
            GameEvent.player_id == player.id,
            GameEvent.event_type.in_(['shot-on-goal', 'goal', 'missed-shot', 'blocked-shot'])
        ).count()
        
        print(f"Player has {player_shot_events} shot events in game_events table")
        
        # Check how many shots in shot_events are associated with this player
        player_shots = db.query(ShotEvent).filter(ShotEvent.shooter_id == player.id).count()
        
        print(f"Player has {player_shots} shots in shot_events table")
        
        # Find shots that are missing player association
        print("\nChecking for shot events that aren't properly linked to shots...")
        
        # Get a sample of shot events for this player
        sample_events = db.query(GameEvent).filter(
            GameEvent.player_id == player.id,
            GameEvent.event_type.in_(['shot-on-goal', 'goal', 'missed-shot', 'blocked-shot'])
        ).limit(5).all()
        
        for event in sample_events:
            # Check if a corresponding ShotEvent exists
            shot = db.query(ShotEvent).filter(ShotEvent.event_id == event.id).first()
            print(f"Event {event.id} ({event.event_type}):")
            print(f"  - Has corresponding shot event: {shot is not None}")
            if shot:
                print(f"  - Shot shooter_id: {shot.shooter_id}")
                print(f"  - Should be: {event.player_id}")
                
                # Fix if needed
                if shot.shooter_id != event.player_id:
                    shot.shooter_id = event.player_id
                    print(f"  - FIXED: shooter_id updated to {event.player_id}")
        
        # Now do a bulk fix for all shots
        print("\nFinding and fixing all unlinked shots...")
        
        # Get all shots with missing shooter IDs
        shots_to_fix = db.query(ShotEvent).join(
            GameEvent, ShotEvent.event_id == GameEvent.id
        ).filter(
            ShotEvent.shooter_id.is_(None) | 
            (ShotEvent.shooter_id != GameEvent.player_id)
        ).all()
        
        print(f"Found {len(shots_to_fix)} shots that need shooter_id fixes")
        
        fixed_count = 0
        for shot in shots_to_fix:
            # Get the corresponding event
            event = db.query(GameEvent).filter(GameEvent.id == shot.event_id).first()
            if event and event.player_id:
                shot.shooter_id = event.player_id
                fixed_count += 1
                
                # Commit every 100 fixes
                if fixed_count % 100 == 0:
                    db.commit()
                    print(f"  - Fixed {fixed_count} shots so far")
        
        # Final commit
        db.commit()
        print(f"Fixed {fixed_count} shots in total")
        
        # Verify fix for the specific player
        player_shots_after = db.query(ShotEvent).filter(ShotEvent.shooter_id == player.id).count()
        print(f"\nAfter fix: Player has {player_shots_after} shots in shot_events table")
    
    else:
        print("Player not found")
        
except Exception as e:
    print(f"Error: {str(e)}")
    import traceback
    traceback.print_exc()
finally:
    db.close()