"""
PuckPattern Models - Simplified approach focused on NHL API data
"""
from sqlalchemy import Column, String, Integer, Float, Date, DateTime, Boolean, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

Base = declarative_base()

# ============================================================================
# CORE ENTITIES (Reference Data)
# ============================================================================

class Season(Base):
    """NHL Seasons - e.g., '2023-24', '2022-23'"""
    __tablename__ = "seasons"
    
    season_id = Column(String, primary_key=True)  # "2023-24"
    start_date = Column(Date)
    end_date = Column(Date)
    is_current = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    player_stats = relationship("PlayerSeasonStats", back_populates="season")
    team_stats = relationship("TeamSeasonStats", back_populates="season")


class Team(Base):
    """NHL Teams"""
    __tablename__ = "teams"
    
    team_id = Column(String, primary_key=True)  # NHL API team ID
    name = Column(String, nullable=False)  # "Toronto Maple Leafs"
    abbreviation = Column(String, nullable=False)  # "TOR"
    city = Column(String)  # "Toronto"
    conference = Column(String)  # "Eastern"
    division = Column(String)  # "Atlantic"
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    player_stats = relationship("PlayerSeasonStats", back_populates="team")
    team_stats = relationship("TeamSeasonStats", back_populates="team")
    rosters = relationship("TeamRoster", back_populates="team")


class Player(Base):
    """NHL Players"""
    __tablename__ = "players"
    
    player_id = Column(String, primary_key=True)  # NHL API player ID
    name = Column(String, nullable=False)
    position = Column(String)  # "C", "LW", "RW", "D", "G"
    birth_date = Column(Date)
    birth_city = Column(String)
    birth_country = Column(String)
    height_inches = Column(Integer)
    weight_pounds = Column(Integer)
    shoots_catches = Column(String)  # "L", "R"
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    season_stats = relationship("PlayerSeasonStats", back_populates="player")
    roster_entries = relationship("TeamRoster", back_populates="player")


class TeamRoster(Base):
    """Team rosters by season - who played for which team when"""
    __tablename__ = "team_rosters"
    
    id = Column(Integer, primary_key=True)
    team_id = Column(String, ForeignKey("teams.team_id"), nullable=False)
    player_id = Column(String, ForeignKey("players.player_id"), nullable=False)
    season_id = Column(String, ForeignKey("seasons.season_id"), nullable=False)
    jersey_number = Column(String)
    position = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    team = relationship("Team", back_populates="rosters")
    player = relationship("Player", back_populates="roster_entries")
    
    # Ensure unique player-team-season combinations
    __table_args__ = (
        UniqueConstraint('team_id', 'player_id', 'season_id', name='unique_roster_entry'),
    )


# ============================================================================
# NHL API STATS (What we collect from their API)
# ============================================================================

class PlayerSeasonStats(Base):
    """Player statistics by season - collected from NHL API"""
    __tablename__ = "player_season_stats"
    
    id = Column(Integer, primary_key=True)
    player_id = Column(String, ForeignKey("players.player_id"), nullable=False)
    season_id = Column(String, ForeignKey("seasons.season_id"), nullable=False)
    team_id = Column(String, ForeignKey("teams.team_id"), nullable=False)
    
    # Basic counting stats
    games_played = Column(Integer, default=0)
    goals = Column(Integer, default=0)
    assists = Column(Integer, default=0)
    points = Column(Integer, default=0)
    shots = Column(Integer, default=0)
    shot_percentage = Column(Float)
    
    # Special teams
    power_play_goals = Column(Integer, default=0)
    power_play_assists = Column(Integer, default=0)
    power_play_points = Column(Integer, default=0)
    short_handed_goals = Column(Integer, default=0)
    short_handed_assists = Column(Integer, default=0)
    short_handed_points = Column(Integer, default=0)
    
    # Physical/defensive
    hits = Column(Integer, default=0)
    blocks = Column(Integer, default=0)
    penalty_minutes = Column(Integer, default=0)
    plus_minus = Column(Integer, default=0)
    
    # Time on ice (in seconds)
    avg_toi = Column(Float)  # Average time on ice per game
    avg_pp_toi = Column(Float)  # Average PP time per game
    avg_sh_toi = Column(Float)  # Average SH time per game
    
    # Face-offs (for centers)
    faceoff_wins = Column(Integer, default=0)
    faceoff_losses = Column(Integer, default=0)
    faceoff_percentage = Column(Float)
    
    # Advanced stats (if available from API)
    corsi_for = Column(Integer)
    corsi_against = Column(Integer)
    fenwick_for = Column(Integer)
    fenwick_against = Column(Integer)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    player = relationship("Player", back_populates="season_stats")
    team = relationship("Team", back_populates="player_stats")
    season = relationship("Season", back_populates="player_stats")
    
    # Ensure unique player-season-team combinations
    __table_args__ = (
        UniqueConstraint('player_id', 'season_id', 'team_id', name='unique_player_season_team'),
    )


class TeamSeasonStats(Base):
    """Team statistics by season - collected from NHL API"""
    __tablename__ = "team_season_stats"
    
    id = Column(Integer, primary_key=True)
    team_id = Column(String, ForeignKey("teams.team_id"), nullable=False)
    season_id = Column(String, ForeignKey("seasons.season_id"), nullable=False)
    
    # Basic team record
    games_played = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    overtime_losses = Column(Integer, default=0)
    points = Column(Integer, default=0)
    
    # Offense
    goals_for = Column(Integer, default=0)
    goals_per_game = Column(Float)
    shots_for = Column(Integer, default=0)
    shots_per_game = Column(Float)
    
    # Defense  
    goals_against = Column(Integer, default=0)
    goals_against_per_game = Column(Float)
    shots_against = Column(Integer, default=0)
    shots_against_per_game = Column(Float)
    
    # Special teams
    power_play_goals = Column(Integer, default=0)
    power_play_opportunities = Column(Integer, default=0)
    power_play_percentage = Column(Float)
    penalty_kill_goals_against = Column(Integer, default=0)
    penalty_kill_opportunities = Column(Integer, default=0)
    penalty_kill_percentage = Column(Float)
    
    # Face-offs
    faceoff_wins = Column(Integer, default=0)
    faceoff_losses = Column(Integer, default=0)
    faceoff_percentage = Column(Float)
    
    # Physical
    hits_for = Column(Integer, default=0)
    hits_against = Column(Integer, default=0)
    blocks_for = Column(Integer, default=0)
    penalty_minutes = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    team = relationship("Team", back_populates="team_stats")
    season = relationship("Season", back_populates="team_stats")
    
    # Ensure unique team-season combinations
    __table_args__ = (
        UniqueConstraint('team_id', 'season_id', name='unique_team_season'),
    )