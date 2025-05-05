from fastapi import APIRouter

router = APIRouter()

@router.get("/teams")
async def get_teams():
    return {"teams": []}

@router.get("/players")
async def get_players():
    return {"players": []}

@router.get("/events")
async def get_events():
    return {"events": []}