from app.db.session import SessionLocal
from app.models.base import Player, Team, GameEvent
from app.models.analytics import Game, ZoneEntry, ShotEvent, Pass, PuckRecovery

db = SessionLocal()

# Check for the player
player = db.query(Player).filter(Player.player_id == '8475768').first()
print(f"Player found: {player.name if player else 'None'}")

# Check for events involving this player
if player:
    events = db.query(GameEvent).filter(GameEvent.player_id == player.id).count()
    print(f"Events for this player: {events}")
    
    # Check for zone entries - specify the join condition explicitly
    entries = db.query(ZoneEntry).join(
        GameEvent, ZoneEntry.event_id == GameEvent.id
    ).filter(
        ZoneEntry.player_id == player.id
    ).count()
    print(f"Zone entries: {entries}")
    
    # Check for shots - specify the join condition explicitly
    shots = db.query(ShotEvent).join(
        GameEvent, ShotEvent.event_id == GameEvent.id
    ).filter(
        ShotEvent.shooter_id == player.id
    ).count()
    print(f"Shots: {shots}")
    
    # Check for passes - specify the join condition explicitly
    passes = db.query(Pass).join(
        GameEvent, Pass.event_id == GameEvent.id
    ).filter(
        Pass.passer_id == player.id
    ).count()
    print(f"Passes: {passes}")
    
    # Check for recoveries - specify the join condition explicitly
    recoveries = db.query(PuckRecovery).join(
        GameEvent, PuckRecovery.event_id == GameEvent.id
    ).filter(
        PuckRecovery.player_id == player.id
    ).count()
    print(f"Recoveries: {recoveries}")

# Check table counts
print("\nTable counts:")
print(f"Teams: {db.query(Team).count()}")
print(f"Players: {db.query(Player).count()}")
print(f"Games: {db.query(Game).count()}")
print(f"Events: {db.query(GameEvent).count()}")
print(f"Shots: {db.query(ShotEvent).count()}")
print(f"Zone Entries: {db.query(ZoneEntry).count()}")
print(f"Passes: {db.query(Pass).count()}")
print(f"Recoveries: {db.query(PuckRecovery).count()}")

db.close()