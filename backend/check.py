# process_all_games.py
from app.db.session import SessionLocal
from app.models.analytics import Game, ShotEvent, ZoneEntry, Pass, PuckRecovery
from app.processing.event_processor import EventProcessor
import traceback

def process_all_games():
    db = SessionLocal()
    processor = EventProcessor(db)
    
    # Get all games 
    games = db.query(Game).all()
    print(f"Found {len(games)} games to process")
    
    # Process each game
    for i, game in enumerate(games):
        if i % 10 == 0:
            print(f"Processing game {i+1} of {len(games)}: {game.game_id}")
        
        try:
            stats = processor.process_game(game.game_id)
            print(f"  - Processed {stats['total_events']} events:")
            print(f"    - Shots: {stats['shots_processed']}")
            print(f"    - Entries: {stats['entries_processed']}")
            print(f"    - Passes: {stats['passes_processed']}")
            print(f"    - Recoveries: {stats['recoveries_processed']}")
            print(f"    - Other: {stats['other_processed']}")
        except Exception as e:
            print(f"Error processing game {game.game_id}: {e}")
            traceback.print_exc()
    
    # Verify counts after processing
    print("\nFinished processing. Counts:")
    print(f"Shots: {db.query(ShotEvent).count()}")
    print(f"Zone Entries: {db.query(ZoneEntry).count()}")
    print(f"Passes: {db.query(Pass).count()}")
    print(f"Recoveries: {db.query(PuckRecovery).count()}")
    
    db.close()
    print("Done!")

if __name__ == "__main__":
    process_all_games()