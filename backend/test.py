# calculate_advanced_metrics.py
from app.db.session import SessionLocal
from app.models.base import Player, GameEvent
from app.models.analytics import Game, PlayerGameStats, ZoneEntry, PuckRecovery, Pass, ShotEvent
from app.services.metrics_service import MetricsService
from sqlalchemy import func
import time

# Create session
db = SessionLocal()

try:
    # Get the metrics service
    metrics_service = MetricsService(db)
    
    # Get all players
    players = db.query(Player).order_by(Player.id).all()
    print(f"Calculating advanced metrics for {len(players)} players...")
    
    start_time = time.time()
    
    total_updated = 0
    
    for i, player in enumerate(players):
        if i % 50 == 0:
            elapsed = time.time() - start_time
            print(f"Processing player {i+1}/{len(players)} [{elapsed:.1f}s elapsed]")
        
        # Calculate metrics for this player
        try:
            # Entry Conversion Rate (ECR)
            ecr = metrics_service.calculate_ecr(player_id=player.id)
            
            # Puck Recovery Impact (PRI)
            pri = metrics_service.calculate_pri(player_id=player.id)
            
            # Positional Disruption Index (PDI)
            pdi = metrics_service.calculate_pdi(player_id=player.id)
            
            # xG Delta from Pass Shot Movement
            xg_delta_psm = metrics_service.calculate_xg_delta_psm(player_id=player.id)
            
            # Update all player game stats with these values
            stats = db.query(PlayerGameStats).filter(
                PlayerGameStats.player_id == player.id
            ).all()
            
            for stat in stats:
                stat.ecr = ecr
                stat.pri = pri
                stat.pdi = pdi
                stat.xg_delta_psm = xg_delta_psm
                total_updated += 1
            
            # Commit in batches
            if (i + 1) % 50 == 0:
                db.commit()
                print(f"  - Committed {total_updated} updates")
                
        except Exception as e:
            print(f"Error calculating metrics for player {player.id}: {str(e)}")
    
    # Final commit
    db.commit()
    
    elapsed = time.time() - start_time
    print(f"\nProcessing complete in {elapsed:.1f} seconds:")
    print(f"  - Updated {total_updated} records with advanced metrics")
    
    # Verify Schwartz's metrics
    schwartz = db.query(Player).filter(Player.player_id == "8475768").first()
    if schwartz:
        stats = db.query(PlayerGameStats).filter(
            PlayerGameStats.player_id == schwartz.id
        ).first()
        
        if stats:
            print(f"\nSchwartz's advanced metrics:")
            print(f"ECR: {stats.ecr}")
            print(f"PRI: {stats.pri}")
            print(f"PDI: {stats.pdi}")
            print(f"xG Delta PSM: {stats.xg_delta_psm}")
    
except Exception as e:
    print(f"Error: {str(e)}")
    import traceback
    traceback.print_exc()
finally:
    db.close()