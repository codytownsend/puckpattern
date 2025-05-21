#!/usr/bin/env python3
from app.db.session import SessionLocal
from app.models.analytics import Game, TeamGameStats, ShotEvent
from app.models.base import Team, GameEvent
from sqlalchemy import func, and_

db = SessionLocal()

# Get all games
games = db.query(Game).all()
print(f"Updating advanced stats for {len(games)} games...")

# Track progress
updated = 0

for i, game in enumerate(games):
    if i % 50 == 0:  # Progress update every 50 games
        print(f"Processing game {i+1}/{len(games)}")
    
    # Process both teams for this game
    for team_id, is_home in [(game.home_team_id, True), (game.away_team_id, False)]:
        # Get team stats record
        stats = db.query(TeamGameStats).filter(
            TeamGameStats.game_id == game.id,
            TeamGameStats.team_id == team_id
        ).first()
        
        if not stats:
            continue
            
        # Calculate Corsi (shot attempts)
        corsi_for = db.query(func.count(GameEvent.id)).filter(
            GameEvent.game_id == game.game_id,
            GameEvent.team_id == team_id,
            GameEvent.event_type.in_(["shot-on-goal", "goal", "missed-shot", "blocked-shot"])
        ).scalar() or 0
        
        opponent_team_id = game.away_team_id if is_home else game.home_team_id
        corsi_against = db.query(func.count(GameEvent.id)).filter(
            GameEvent.game_id == game.game_id,
            GameEvent.team_id == opponent_team_id,
            GameEvent.event_type.in_(["shot-on-goal", "goal", "missed-shot", "blocked-shot"])
        ).scalar() or 0
        
        # Calculate power play opportunities and goals
        pp_events = db.query(GameEvent).filter(
            GameEvent.game_id == game.game_id,
            GameEvent.team_id != team_id,  # Other team committed penalties
            GameEvent.event_type == "penalty"
        ).count()
        
        pp_goals = db.query(func.count(GameEvent.id)).filter(
            GameEvent.game_id == game.game_id,
            GameEvent.team_id == team_id,
            GameEvent.event_type == "goal",
            GameEvent.situation_code.like("PP%")  # PP situations
        ).scalar() or 0
        
        # Calculate pk opportunities and goals against
        pk_events = db.query(GameEvent).filter(
            GameEvent.game_id == game.game_id,
            GameEvent.team_id == team_id,  # This team committed penalties
            GameEvent.event_type == "penalty"
        ).count()
        
        pk_goals_against = db.query(func.count(GameEvent.id)).filter(
            GameEvent.game_id == game.game_id,
            GameEvent.team_id != team_id,
            GameEvent.event_type == "goal",
            GameEvent.situation_code.like("PP%")  # PP situations (PK for this team)
        ).scalar() or 0
        
        # Calculate xG from shot events
        xg = db.query(func.sum(ShotEvent.xg)).join(
            GameEvent, ShotEvent.event_id == GameEvent.id
        ).filter(
            GameEvent.game_id == game.game_id,
            GameEvent.team_id == team_id
        ).scalar() or 0.0
        
        xg_against = db.query(func.sum(ShotEvent.xg)).join(
            GameEvent, ShotEvent.event_id == GameEvent.id
        ).filter(
            GameEvent.game_id == game.game_id,
            GameEvent.team_id != team_id
        ).scalar() or 0.0
        
        # Update the team stats
        stats.corsi_for = corsi_for
        stats.corsi_against = corsi_against
        stats.pp_opportunities = pp_events
        stats.pp_goals = pp_goals
        stats.pk_times_shorthanded = pk_events
        stats.pk_goals_against = pk_goals_against
        stats.xg = xg
        stats.xg_against = xg_against
        
        updated += 1
        
        # Commit every 100 updates
        if updated % 100 == 0:
            db.commit()
            print(f"Updated {updated} team stat records")

# Final commit
db.commit()
print(f"Advanced stats update complete! Updated {updated} team stat records")
db.close()