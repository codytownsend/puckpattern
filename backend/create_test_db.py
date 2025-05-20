import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent))

from app.models.base import Base
from app.db.session import engine

def create_test_tables():
    """Create all tables in the test database."""
    print("Creating test database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully")

if __name__ == "__main__":
    create_test_tables()