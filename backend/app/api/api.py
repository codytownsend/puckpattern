from fastapi import APIRouter
from app.api.endpoints import simple_stats

api_router = APIRouter()

# Include our new simple stats endpoints
api_router.include_router(simple_stats.router, prefix="/stats", tags=["stats"])

# Health check endpoint
@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "message": "PuckPattern API is running"}

@api_router.get("/")
async def root():
    return {
        "message": "Welcome to PuckPattern API v2",
        "description": "Simplified hockey analytics focused on NHL API data",
        "endpoints": {
            "/stats/seasons": "Get available seasons",
            "/stats/teams": "Get all teams",
            "/stats/players": "Get players (with search)",
            "/stats/teams/{team_id}/stats": "Get team statistics",
            "/stats/teams/{team_id}/roster": "Get team roster",
            "/stats/players/{player_id}/stats": "Get player statistics",
            "/stats/summary": "Database summary"
        }
    }