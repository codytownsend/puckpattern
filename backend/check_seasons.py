from app.db.session import SessionLocal
from app.models.analytics import Game
from sqlalchemy import distinct

# Create a session
db = SessionLocal()

try:
    # Query distinct seasons
    seasons = db.query(distinct(Game.season)).order_by(Game.season).all()
    
    # Display results
    if seasons:
        print("Seasons in the database:")
        for season in seasons:
            # Extract the season value from the tuple
            season_value = season[0]
            print(f"- {season_value}")
        print(f"Total: {len(seasons)} seasons")
    else:
        print("No seasons found in the database.")
    
    # Additional statistics
    game_count = db.query(Game).count()
    print(f"\nTotal games in database: {game_count}")
    
    # Games per season breakdown
    print("\nGames per season:")
    season_counts = db.query(Game.season, db.func.count(Game.id)).group_by(Game.season).order_by(Game.season).all()
    for season, count in season_counts:
        print(f"- {season}: {count} games")
        
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()