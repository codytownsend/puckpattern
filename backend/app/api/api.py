from fastapi import APIRouter

from app.api.endpoints import teams, players, games, shots, entries, metrics, profiles, powerplay, system

api_router = APIRouter()

# Core data endpoints
api_router.include_router(teams.router, prefix="/teams", tags=["teams"])
api_router.include_router(players.router, prefix="/players", tags=["players"])
api_router.include_router(games.router, prefix="/games", tags=["games"])

# Event data endpoints
api_router.include_router(shots.router, prefix="/shots", tags=["shots"])
api_router.include_router(entries.router, prefix="/entries", tags=["zone entries"])

# Analytics endpoints
api_router.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
api_router.include_router(profiles.router, prefix="/profiles", tags=["profiles"])
api_router.include_router(powerplay.router, prefix="/powerplay", tags=["power play"])
api_router.include_router(system.router, prefix="/system", tags=["system"])