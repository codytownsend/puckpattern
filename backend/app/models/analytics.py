from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, JSON, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.models.base import Base, Team, Player, GameEvent

# Many-to-many relationship for players and games
player_game = Table(
    'player_game',
    Base.metadata,
    Column('player_id', Integer, ForeignKey('players.id')),
    Column('game_id', Integer, ForeignKey('games.id'))
)

class Game(Base):
    __tablename__ = "games"
    
    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(String, unique=True, index=True)
    date = Column(DateTime)
    home_team_id = Column(Integer, ForeignKey("teams.id"))
    away_team_id = Column(Integer, ForeignKey("teams.id"))
    season = Column(String)
    status = Column(String)
    period = Column(Integer)
    time_remaining = Column(String)
    home_score = Column(Integer)
    away_score = Column(Integer)
    venue_name = Column(String)
    venue_city = Column(String)
    game_type = Column(Integer)  # 2 for regular season, 3 for playoffs
    neutral_site = Column(Boolean, default=False)
    eastern_utc_offset = Column(String)
    venue_utc_offset = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    home_team = relationship("Team", foreign_keys=[home_team_id])
    away_team = relationship("Team", foreign_keys=[away_team_id])
    players = relationship("Player", secondary=player_game, back_populates="games")
    events = relationship("GameEvent", back_populates="game")

# Add relationship to Player model
Player.games = relationship("Game", secondary=player_game, back_populates="players")
# Add relationship to GameEvent model
GameEvent.game = relationship("Game", back_populates="events")

class ShotEvent(Base):
    __tablename__ = "shot_events"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("game_events.id"))
    shot_type = Column(String)
    distance = Column(Float)
    angle = Column(Float)
    goal = Column(Boolean, default=False)
    xg = Column(Float)  # Expected goals value
    shooter_id = Column(Integer, ForeignKey("players.id"))
    goalie_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    primary_assist_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    secondary_assist_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    preceding_event_id = Column(Integer, ForeignKey("game_events.id"), nullable=True)
    is_scoring_chance = Column(Boolean, default=False)
    is_high_danger = Column(Boolean, default=False)
    rush_shot = Column(Boolean, default=False)
    rebound_shot = Column(Boolean, default=False)
    frozen_shot = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    event = relationship("GameEvent")
    shooter = relationship("Player", foreign_keys=[shooter_id])
    goalie = relationship("Player", foreign_keys=[goalie_id])
    primary_assist = relationship("Player", foreign_keys=[primary_assist_id])
    secondary_assist = relationship("Player", foreign_keys=[secondary_assist_id])
    preceding_event = relationship("GameEvent", foreign_keys=[preceding_event_id])

class ZoneEntry(Base):
    __tablename__ = "zone_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("game_events.id"))
    entry_type = Column(String)  # "carry", "dump", "pass"
    controlled = Column(Boolean)
    player_id = Column(Integer, ForeignKey("players.id"))
    defender_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    lead_to_shot = Column(Boolean, default=False)
    lead_to_shot_time = Column(Float, nullable=True)  # Time in seconds to shot
    attack_speed = Column(String, nullable=True)  # "RUSH", "CONTROLLED", etc.
    sequence_number = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    event = relationship("GameEvent")
    player = relationship("Player", foreign_keys=[player_id])
    defender = relationship("Player", foreign_keys=[defender_id])

class Pass(Base):
    __tablename__ = "passes"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("game_events.id"))
    passer_id = Column(Integer, ForeignKey("players.id"))
    recipient_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    pass_type = Column(String)  # "direct", "saucer", "bounce", etc.
    zone = Column(String)  # "OZ", "NZ", "DZ"
    completed = Column(Boolean)
    intercepted = Column(Boolean, default=False)
    intercepted_by_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    distance = Column(Float, nullable=True)  # Distance in feet
    angle_change = Column(Float, nullable=True)  # Change in angle of attack
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    event = relationship("GameEvent")
    passer = relationship("Player", foreign_keys=[passer_id])
    recipient = relationship("Player", foreign_keys=[recipient_id])
    intercepted_by = relationship("Player", foreign_keys=[intercepted_by_id])

class PuckRecovery(Base):
    __tablename__ = "puck_recoveries"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("game_events.id"))
    player_id = Column(Integer, ForeignKey("players.id"))
    zone = Column(String)  # "OZ", "NZ", "DZ"
    recovery_type = Column(String)  # "loose", "forecheck", "takeaway"
    lead_to_possession = Column(Boolean)
    preceded_by_id = Column(Integer, ForeignKey("game_events.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    event = relationship("GameEvent")
    player = relationship("Player")
    preceded_by = relationship("GameEvent", foreign_keys=[preceded_by_id])

class Shift(Base):
    __tablename__ = "shifts"
    
    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"))
    player_id = Column(Integer, ForeignKey("players.id"))
    start_time = Column(Float)  # Seconds from start of period
    end_time = Column(Float)  # Seconds from start of period
    duration = Column(Float)  # Duration in seconds
    period = Column(Integer)
    team_id = Column(Integer, ForeignKey("teams.id"))
    on_ice_strength = Column(String)  # "EV", "PP", "SH"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    game = relationship("Game")
    player = relationship("Player")
    team = relationship("Team")

class PowerPlay(Base):
    __tablename__ = "power_plays"
    
    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"))
    team_id = Column(Integer, ForeignKey("teams.id"))
    start_time = Column(Float)
    end_time = Column(Float)
    period = Column(Integer)
    duration = Column(Float)
    advantage_type = Column(String)  # "5v4", "5v3", etc.
    successful = Column(Boolean)
    pp_formation = Column(String, nullable=True)  # Detected formation
    pp_shots = Column(Integer, default=0)
    pp_shot_attempts = Column(Integer, default=0)
    pp_zone_time = Column(Float, nullable=True)  # Time in offensive zone in seconds
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    game = relationship("Game")
    team = relationship("Team")
    events = relationship("GameEvent", primaryjoin="and_(PowerPlay.game_id==GameEvent.game_id, PowerPlay.team_id==GameEvent.team_id, PowerPlay.start_time<=GameEvent.time_elapsed, PowerPlay.end_time>=GameEvent.time_elapsed, PowerPlay.period==GameEvent.period)")

class PlayerGameStats(Base):
    __tablename__ = "player_game_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id"))
    game_id = Column(Integer, ForeignKey("games.id"))
    team_id = Column(Integer, ForeignKey("teams.id"))
    
    # Basic stats
    toi = Column(Float)  # Time on ice in seconds
    goals = Column(Integer, default=0)
    assists = Column(Integer, default=0)
    shots = Column(Integer, default=0)
    hits = Column(Integer, default=0)
    blocks = Column(Integer, default=0)
    pim = Column(Integer, default=0)  # Penalty minutes
    
    # Advanced metrics
    xg = Column(Float, default=0.0)  # Expected goals
    xg_against = Column(Float, default=0.0)  # Expected goals against
    corsi_for = Column(Integer, default=0)
    corsi_against = Column(Integer, default=0)
    zone_starts_off = Column(Integer, default=0)
    zone_starts_def = Column(Integer, default=0)
    zone_starts_neutral = Column(Integer, default=0)
    
    # Face-offs
    faceoffs_taken = Column(Integer, default=0)
    faceoffs_won = Column(Integer, default=0)
    faceoff_pct = Column(Float, nullable=True)
    
    # Power play
    pp_toi = Column(Float, default=0.0)  # PP time on ice in seconds
    pp_goals = Column(Integer, default=0)
    pp_assists = Column(Integer, default=0)
    pp_shots = Column(Integer, default=0)
    
    # Penalty kill
    pk_toi = Column(Float, default=0.0)  # PK time on ice in seconds
    pk_goals_against = Column(Integer, default=0)
    pk_shots_against = Column(Integer, default=0)
    
    # Custom metrics
    ecr = Column(Float, nullable=True)  # Entry Conversion Rate
    pri = Column(Float, nullable=True)  # Puck Recovery Impact
    pdi = Column(Float, nullable=True)  # Positional Disruption Index
    xg_delta_psm = Column(Float, nullable=True)  # xGΔPSM
    sfs = Column(Float, nullable=True)  # System Fidelity Score
    omc = Column(Float, nullable=True)  # Offensive Momentum Curve
    ice_plus = Column(Float, nullable=True)  # ICE+ Composite Score
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    player = relationship("Player")
    game = relationship("Game")
    team = relationship("Team")

class TeamGameStats(Base):
    __tablename__ = "team_game_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"))
    game_id = Column(Integer, ForeignKey("games.id"))
    
    # Basic stats
    goals = Column(Integer, default=0)
    shots = Column(Integer, default=0)
    hits = Column(Integer, default=0)
    blocks = Column(Integer, default=0)
    pim = Column(Integer, default=0)  # Penalty minutes
    faceoff_wins = Column(Integer, default=0)
    faceoff_losses = Column(Integer, default=0)
    
    # Advanced metrics
    xg = Column(Float, default=0.0)  # Expected goals
    xg_against = Column(Float, default=0.0)  # Expected goals against
    corsi_for = Column(Integer, default=0)
    corsi_against = Column(Integer, default=0)
    
    # Power play
    pp_opportunities = Column(Integer, default=0)
    pp_goals = Column(Integer, default=0)
    pp_time = Column(Float, default=0.0)  # PP time in seconds
    pp_shots = Column(Integer, default=0)
    
    # Penalty kill
    pk_times_shorthanded = Column(Integer, default=0)
    pk_goals_against = Column(Integer, default=0)
    pk_time = Column(Float, default=0.0)  # PK time in seconds
    
    # System detection
    forecheck_style = Column(String, nullable=True)
    defensive_structure = Column(String, nullable=True)
    pp_formation = Column(String, nullable=True)
    pk_formation = Column(String, nullable=True)
    
    # Custom metrics
    team_ecr = Column(Float, nullable=True)  # Team Entry Conversion Rate
    team_pri = Column(Float, nullable=True)  # Team Puck Recovery Impact
    team_pdi = Column(Float, nullable=True)  # Team Positional Disruption Index
    system_metrics = Column(JSON, nullable=True)  # Detailed system metrics
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    team = relationship("Team")
    game = relationship("Game")

class TeamProfile(Base):
    __tablename__ = "team_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"))
    season = Column(String)
    
    # Strategy vectors (JSON format for flexibility)
    offensive_style = Column(JSON)  # Components: tempo, shot selection, entry style
    defensive_style = Column(JSON)  # Components: forecheck, neutral zone, defensive zone
    special_teams = Column(JSON)  # Components: PP formations, PK formations
    
    # Overall profile data
    team_fingerprint = Column(JSON)  # Complete vector representation
    similar_teams = Column(JSON, nullable=True)  # IDs and similarity scores of similar teams
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    team = relationship("Team")

class PlayerProfile(Base):
    __tablename__ = "player_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id"))
    season = Column(String)
    
    # Role detection
    primary_role = Column(String)
    secondary_role = Column(String, nullable=True)
    
    # Behavioral vectors
    offensive_behavior = Column(JSON)  # Shot selection, passing tendencies, etc.
    defensive_behavior = Column(JSON)  # Positioning, disruption patterns, etc.
    transition_behavior = Column(JSON)  # Entry/exit styles, etc.
    
    # System fit data
    current_team_fit = Column(Float)
    optimal_system_type = Column(String, nullable=True)
    system_fit_scores = Column(JSON, nullable=True)  # Fit scores for all teams
    
    # Composite metrics
    season_ice_plus = Column(Float, nullable=True)
    consistency_metrics = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    player = relationship("Player")