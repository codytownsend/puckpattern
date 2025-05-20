# Create a new file: backend/tests/test_services.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import get_db, Base
from app.services.metrics_service import MetricsService
from app.services.sequence_service import SequenceService
from app.models.base import Team, Player

# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_services.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module")
def test_db():
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create test data
    db = TestingSessionLocal()
    # Add test teams, players, events, etc.
    
    yield db
    
    # Clean up
    Base.metadata.drop_all(bind=engine)

def test_calculate_ecr(test_db):
    """Test Entry Conversion Rate calculation."""
    service = MetricsService(test_db)
    # Add test data and test calculations
    # ...