import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.session import get_db, Base
from app.models.base import Team, Player, GameEvent
from app.models.analytics import Game, ShotEvent, ZoneEntry

# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override the dependency
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(scope="module")
def test_db():
    # Create the database
    Base.metadata.create_all(bind=engine)
    
    # Create test data
    db = TestingSessionLocal()
    
    # Create teams
    team1 = Team(team_id=1, name="Toronto Maple Leafs", abbreviation="TOR")
    team2 = Team(team_id=2, name="Montreal Canadiens", abbreviation="MTL")
    db.add(team1)
    db.add(team2)
    db.commit()
    
    # Create players
    player1 = Player(player_id=8471675, name="Sidney Crosby", team_id=1, position="C")
    player2 = Player(player_id=8471214, name="Alex Ovechkin", team_id=2, position="LW")
    db.add(player1)
    db.add(player2)
    db.commit()
    
    # Create game
    game = Game(
        game_id="2022020001",
        date="2022-10-01T00:00:00",
        home_team_id=1,
        away_team_id=2,
        season="20222023",
        status="Final",
        period=3,
        time_remaining="00:00",
        home_score=3,
        away_score=2
    )
    db.add(game)
    db.commit()
    
    # Create game events
    event1 = GameEvent(
        game_id="2022020001",
        event_type="SHOT",
        period=1,
        time_elapsed=120.0,
        x_coordinate=50.0,
        y_coordinate=20.0,
        player_id=1,
        team_id=1
    )
    db.add(event1)
    db.commit()
    
    # Create shot event
    shot = ShotEvent(
        event_id=1,
        shot_type="Wrist Shot",
        distance=25.0,
        angle=15.0,
        goal=False,
        shooter_id=1,
        goalie_id=None,
        xg=0.05
    )
    db.add(shot)
    
    # Create zone entry
    entry = ZoneEntry(
        event_id=1,
        entry_type="carry",
        controlled=True,
        player_id=1,
        lead_to_shot=True,
        lead_to_shot_time=5.0
    )
    db.add(entry)
    db.commit()
    
    # Test data is set up
    yield db
    
    # Clean up
    Base.metadata.drop_all(bind=engine)


def test_root(test_db):
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to PuckPattern API"}


def test_get_teams(test_db):
    """Test getting all teams."""
    response = client.get("/api/teams/")
    assert response.status_code == 200
    data = response.json()
    assert "teams" in data
    assert len(data["teams"]) == 2
    assert data["teams"][0]["name"] == "Toronto Maple Leafs"
    assert data["teams"][1]["name"] == "Montreal Canadiens"


def test_get_team(test_db):
    """Test getting a specific team."""
    response = client.get("/api/teams/1")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Toronto Maple Leafs"
    assert data["abbreviation"] == "TOR"


def test_get_nonexistent_team(test_db):
    """Test getting a team that doesn't exist."""
    response = client.get("/api/teams/999")
    assert response.status_code == 404


def test_create_team(test_db):
    """Test creating a new team."""
    new_team = {
        "team_id": 3,
        "name": "Boston Bruins",
        "abbreviation": "BOS"
    }
    response = client.post("/api/teams/", json=new_team)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Boston Bruins"
    assert data["abbreviation"] == "BOS"
    
    # Verify it was actually created
    response = client.get("/api/teams/3")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Boston Bruins"


def test_update_team(test_db):
    """Test updating a team."""
    update_data = {
        "name": "Toronto Maple Leafs Updated"
    }
    response = client.put("/api/teams/1", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Toronto Maple Leafs Updated"
    
    # Verify it was actually updated
    response = client.get("/api/teams/1")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Toronto Maple Leafs Updated"


def test_delete_team(test_db):
    """Test deleting a team."""
    # Create a team to delete
    new_team = {
        "team_id": "4",
        "name": "New York Rangers",
        "abbreviation": "NYR"
    }
    client.post("/api/teams/", json=new_team)
    
    # Delete the team
    response = client.delete("/api/teams/4")
    assert response.status_code == 200
    
    # Verify it was deleted
    response = client.get("/api/teams/4")
    assert response.status_code == 404


def test_get_players(test_db):
    """Test getting all players."""
    response = client.get("/api/players/")
    assert response.status_code == 200
    data = response.json()
    assert "players" in data
    assert len(data["players"]) == 2
    assert data["players"][0]["name"] == "Sidney Crosby"
    assert data["players"][1]["name"] == "Alex Ovechkin"


def test_get_player(test_db):
    """Test getting a specific player."""
    response = client.get("/api/players/8471675")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Sidney Crosby"
    assert data["position"] == "C"


def test_get_player_stats(test_db):
    """Test getting player stats."""
    response = client.get("/api/players/8471675/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["player_id"] == 8471675
    assert data["name"] == "Sidney Crosby"
    assert "games_played" in data


def test_get_games(test_db):
    """Test getting all games."""
    response = client.get("/api/games/")
    assert response.status_code == 200
    data = response.json()
    assert "games" in data
    assert len(data["games"]) == 1
    assert data["games"][0]["game_id"] == "2022020001"


def test_get_game(test_db):
    """Test getting a specific game."""
    response = client.get("/api/games/2022020001")
    assert response.status_code == 200
    data = response.json()
    assert data["game_id"] == "2022020001"
    assert data["home_score"] == 3
    assert data["away_score"] == 2


def test_get_game_stats(test_db):
    """Test getting game stats."""
    response = client.get("/api/games/2022020001/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["game_id"] == "2022020001"
    assert "home_team" in data
    assert "away_team" in data


def test_get_events(test_db):
    """Test getting game events."""
    response = client.get("/api/events/")
    assert response.status_code == 200
    data = response.json()
    assert "events" in data
    assert len(data["events"]) == 1
    assert data["events"][0]["event_type"] == "SHOT"


def test_get_event(test_db):
    """Test getting a specific event."""
    response = client.get("/api/events/1")
    assert response.status_code == 200
    data = response.json()
    assert data["event_type"] == "SHOT"
    assert data["period"] == 1


def test_get_entries(test_db):
    """Test getting zone entries."""
    response = client.get("/api/entries/")
    assert response.status_code == 200
    data = response.json()
    assert "entries" in data
    assert len(data["entries"]) == 1
    assert data["entries"][0]["entry_type"] == "carry"
    assert data["entries"][0]["controlled"] is True


def test_get_entry(test_db):
    """Test getting a specific zone entry."""
    response = client.get("/api/entries/1")
    assert response.status_code == 200
    data = response.json()
    assert data["entry_type"] == "carry"
    assert data["controlled"] is True


def test_get_player_entries_stats(test_db):
    """Test getting player zone entry stats."""
    response = client.get("/api/entries/player/8471675/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["player_id"] == 8471675
    assert data["name"] == "Sidney Crosby"
    assert "total_entries" in data
    assert "controlled_entries" in data


def test_get_player_metrics(test_db):
    """Test getting player metrics."""
    response = client.get("/api/metrics/player/8471675")
    assert response.status_code == 200
    data = response.json()
    assert data["player_id"] == 8471675
    assert data["name"] == "Sidney Crosby"
    assert "ecr" in data
    assert "pri" in data
    assert "shot_metrics" in data
    assert "ice_plus" in data


def test_get_team_metrics(test_db):
    """Test getting team metrics."""
    response = client.get("/api/metrics/team/1")
    assert response.status_code == 200
    data = response.json()
    assert data["team_id"] == 1
    assert data["name"] == "Toronto Maple Leafs Updated"  # Updated name from previous test
    assert "ecr" in data
    assert "pri" in data
    assert "shot_metrics" in data