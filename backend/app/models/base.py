from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class Team(Base):
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, unique=True, index=True)
    name = Column(String, index=True)
    abbreviation = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    city_name = Column(String)
    team_name = Column(String)  # Team name without city
    division = Column(String)
    conference = Column(String)
    franchise_id = Column(Integer)
    venue_name = Column(String)
    venue_city = Column(String)
    official_site_url = Column(String)
    active = Column(Boolean, default=True)

class Player(Base):
    __tablename__ = "players"
    
    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, unique=True, index=True)
    name = Column(String, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"))
    position = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    player_slug = Column(String)  # URL-friendly identifier
    sweater_number = Column(String)
    height_in_inches = Column(Integer)
    height_in_cm = Column(Float)
    weight_in_pounds = Column(Integer) 
    weight_in_kg = Column(Float)
    birth_date = Column(Date)
    birth_city = Column(String)
    birth_state_province = Column(String)
    birth_country = Column(String)
    shoots_catches = Column(String)
    headshot_url = Column(String)

class GameEvent(Base):
    __tablename__ = "game_events"
    
    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(String, ForeignKey("games.game_id"), index=True)
    event_type = Column(String, index=True)
    period = Column(Integer)
    time_elapsed = Column(Float)
    x_coordinate = Column(Float)
    y_coordinate = Column(Float)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    team_id = Column(Integer, ForeignKey("teams.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # Add to existing GameEvent class
    situation_code = Column(String)  # e.g., "EV", "PP", "SH"
    strength_code = Column(String)
    is_scoring_play = Column(Boolean, default=False)
    is_penalty = Column(Boolean, default=False)
    sort_order = Column(Integer)  # For ordering events chronologically
    event_id = Column(Integer)  # NHL event ID
    time_remaining = Column(String)  # Time remaining in period