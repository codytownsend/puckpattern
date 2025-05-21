#!/usr/bin/env python3
from app.db.session import SessionLocal
from app.models.analytics import Game, TeamGameStats
from app.models.base import Team, GameEvent
from sqlalchemy import func

db = SessionLocal()

# Get all games
games = db.query(Game).all()
print(f"Processing {len(games)} games...")

# Track progress
processed = 0
skipped = 0

for i, game in enumerate(games):
    if i % 50 == 0:  # Progress update every 50 games
        print(f"Processing game {i+1}/{len(games)}")
    
    # Check if home team stats exist
    home_stats = db.query(TeamGameStats).filter(
        TeamGameStats.game_id == game.id,
        TeamGameStats.team_id == game.home_team_id
    ).first()
    
    # Check if away team stats exist
    away_stats = db.query(TeamGameStats).filter(
        TeamGameStats.game_id == game.id,
        TeamGameStats.team_id == game.away_team_id
    ).first()
    
    if home_stats and away_stats:
        skipped += 1
        continue
    
    # Process both teams for this game
    for team_id, is_home in [(game.home_team_id, True), (game.away_team_id, False)]:
        # Skip if stats already exist
        if (is_home and home_stats) or (not is_home and away_stats):
            continue
            
        # Count stats for this team in this game - using correct event types
        shots = db.query(func.count(GameEvent.id)).filter(
            GameEvent.game_id == game.game_id,
            GameEvent.team_id == team_id,
            GameEvent.event_type.in_(["shot-on-goal", "goal", "missed-shot"])
        ).scalar() or 0
        
        goals = db.query(func.count(GameEvent.id)).filter(
            GameEvent.game_id == game.game_id,
            GameEvent.team_id == team_id,
            GameEvent.event_type == "goal"
        ).scalar() or 0
        
        hits = db.query(func.count(GameEvent.id)).filter(
            GameEvent.game_id == game.game_id,
            GameEvent.team_id == team_id,
            GameEvent.event_type == "hit"
        ).scalar() or 0
        
        blocks = db.query(func.count(GameEvent.id)).filter(
            GameEvent.game_id == game.game_id,
            GameEvent.team_id == team_id,
            GameEvent.event_type == "blocked-shot"
        ).scalar() or 0
        
        # Count faceoffs
        faceoff_events = db.query(GameEvent).filter(
            GameEvent.game_id == game.game_id,
            GameEvent.event_type == "faceoff"
        ).all()
        
        faceoff_wins = 0
        for faceoff in faceoff_events:
            if faceoff.team_id == team_id:
                faceoff_wins += 1
                
        faceoff_losses = len(faceoff_events) - faceoff_wins
        
        # Create team game stats record
        team_stats = TeamGameStats(
            team_id=team_id,
            game_id=game.id,
            goals=goals,
            shots=shots,
            hits=hits,
            blocks=blocks,
            faceoff_wins=faceoff_wins,
            faceoff_losses=faceoff_losses
        )
        
        db.add(team_stats)
        processed += 1
        
        # Commit every 100 records to avoid large transactions
        if processed % 100 == 0:
            db.commit()
            print(f"Saved {processed} team stat records")

# Final commit
db.commit()
print(f"Team stats calculation complete!")
print(f"- {processed} team stat records created")
print(f"- {skipped} games skipped (already had stats)")