#!/usr/bin/env python3
"""
Test script for verifying services in isolation.
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent))

from app.db.session import SessionLocal
from app.services.metrics_service import MetricsService
from app.services.sequence_service import SequenceService

# Create a DB session
db = SessionLocal()

# Create service instances
metrics_service = MetricsService(db)
sequence_service = SequenceService(db)

# Test player metrics for a known player
player_id = 8475768  # Use an ID you know exists in your DB
print(f"Testing metrics for player {player_id}:")
ecr = metrics_service.calculate_ecr(player_id=player_id)
pri = metrics_service.calculate_pri(player_id=player_id)
pdi = metrics_service.calculate_pdi(player_id=player_id)
xg_delta = metrics_service.calculate_xg_delta_psm(player_id=player_id)
print(f"ECR: {ecr}")
print(f"PRI: {pri}")
print(f"PDI: {pdi}")
print(f"xG Delta PSM: {xg_delta}")

# Test team metrics for a known team
team_id = 1  # Use a team ID you know exists
print(f"\nTesting metrics for team {team_id}:")
team_ecr = metrics_service.calculate_ecr(team_id=team_id)
team_pri = metrics_service.calculate_pri(team_id=team_id)
team_pdi = metrics_service.calculate_pdi(team_id=team_id)
print(f"Team ECR: {team_ecr}")
print(f"Team PRI: {team_pri}")
print(f"Team PDI: {team_pdi}")

# Test sequence detection for a known game
game_id = "2023030417"  # Use a game ID you know exists
print(f"\nTesting sequence detection for game {game_id}:")
cycles = sequence_service.detect_cycles(game_id=game_id, team_id=team_id)
rushes = sequence_service.detect_rush_plays(game_id=game_id, team_id=team_id)
print(f"Found {len(cycles)} cycle sequences")
print(f"Found {len(rushes)} rush plays")

# Close the DB session
db.close()