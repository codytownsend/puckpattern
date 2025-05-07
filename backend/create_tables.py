#!/usr/bin/env python3
# create_tables.py

import sys
import os
from sqlalchemy import MetaData, Table, Column, ForeignKey, Integer, String, Float, DateTime, Boolean, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.schema import CreateTable

# Add the backend directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.db.session import engine, Base
from app.core.config import settings

def create_tables_manually():
    """
    Create tables in the correct order to avoid circular dependencies.
    """
    metadata = MetaData()
    
    # 1. Create teams table
    teams = Table(
        'teams',
        metadata,
        Column('id', Integer, primary_key=True),
        Column('team_id', String, index=True),
        Column('name', String, index=True),
        Column('abbreviation', String),
        Column('created_at', DateTime(timezone=True), server_default=func.now()),
        Column('updated_at', DateTime(timezone=True)),
        Column('city_name', String),
        Column('team_name', String),
        Column('division', String),
        Column('conference', String),
        Column('franchise_id', Integer),
        Column('venue_name', String),
        Column('venue_city', String),
        Column('official_site_url', String),
        Column('active', Boolean, default=True),
        UniqueConstraint('team_id', name='uq_teams_team_id')
    )
    
    # 2. Create players table
    players = Table(
        'players',
        metadata,
        Column('id', Integer, primary_key=True),
        Column('player_id', String, index=True),
        Column('name', String, index=True),
        Column('team_id', Integer, ForeignKey('teams.id')),
        Column('position', String),
        Column('created_at', DateTime(timezone=True), server_default=func.now()),
        Column('updated_at', DateTime(timezone=True)),
        Column('player_slug', String),
        Column('sweater_number', String),
        Column('height_in_inches', Integer),
        Column('height_in_cm', Float),
        Column('weight_in_pounds', Integer),
        Column('weight_in_kg', Float),
        Column('birth_date', DateTime),
        Column('birth_city', String),
        Column('birth_state_province', String),
        Column('birth_country', String),
        Column('shoots_catches', String),
        Column('headshot_url', String),
        UniqueConstraint('player_id', name='uq_players_player_id')
    )
    
    # 3. Create games table
    games = Table(
        'games',
        metadata,
        Column('id', Integer, primary_key=True),
        Column('game_id', String, index=True),
        Column('date', DateTime),
        Column('home_team_id', Integer, ForeignKey('teams.id')),
        Column('away_team_id', Integer, ForeignKey('teams.id')),
        Column('season', String),
        Column('status', String),
        Column('period', Integer),
        Column('time_remaining', String),
        Column('home_score', Integer),
        Column('away_score', Integer),
        Column('venue_name', String),
        Column('venue_city', String),
        Column('game_type', Integer),
        Column('neutral_site', Boolean, default=False),
        Column('eastern_utc_offset', String),
        Column('venue_utc_offset', String),
        Column('created_at', DateTime(timezone=True), server_default=func.now()),
        Column('updated_at', DateTime(timezone=True)),
        UniqueConstraint('game_id', name='uq_games_game_id')
    )
    
    # 4. Create the player_game table
    player_game = Table(
        'player_game',
        metadata,
        Column('player_id', Integer, ForeignKey('players.id')),
        Column('game_id', Integer, ForeignKey('games.id'))
    )
    
    # 5. Create game_events table
    game_events = Table(
        'game_events',
        metadata,
        Column('id', Integer, primary_key=True),
        Column('game_id', String, ForeignKey('games.game_id'), index=True),
        Column('event_type', String, index=True),
        Column('period', Integer),
        Column('time_elapsed', Float),
        Column('x_coordinate', Float),
        Column('y_coordinate', Float),
        Column('player_id', Integer, ForeignKey('players.id'), nullable=True),
        Column('team_id', Integer, ForeignKey('teams.id')),
        Column('time_remaining', String),
        Column('situation_code', String),
        Column('strength_code', String),
        Column('is_scoring_play', Boolean),
        Column('is_penalty', Boolean),
        Column('sort_order', Integer),
        Column('event_id', Integer),
        Column('created_at', DateTime(timezone=True), server_default=func.now())
    )
    
    # Create the tables in order
    conn = engine.connect()
    
    try:
        print("Creating teams table...")
        conn.execute(CreateTable(teams))
        
        print("Creating players table...")
        conn.execute(CreateTable(players))
        
        print("Creating games table...")
        conn.execute(CreateTable(games))
        
        print("Creating player_game table...")
        conn.execute(CreateTable(player_game))
        
        print("Creating game_events table...")
        conn.execute(CreateTable(game_events))
        
        # Now create the remaining tables using SQLAlchemy models
        print("Creating remaining tables...")
        
        # Define the tables to create in a specific order to avoid circular dependencies
        remaining_tables = [
            "shot_events",
            "zone_entries",
            "passes",
            "puck_recoveries",
            "shifts",
            "power_plays",
            "player_game_stats",
            "team_game_stats",
            "team_profiles",
            "player_profiles"
        ]
        
        for table_name in remaining_tables:
            try:
                # Find the table in the metadata
                for table in Base.metadata.sorted_tables:
                    if table.name == table_name:
                        print(f"Creating {table_name} table...")
                        conn.execute(CreateTable(table))
                        break
            except Exception as e:
                print(f"Error creating {table_name}: {e}")
                raise
        
        conn.commit()
        print("Tables created successfully!")
    except Exception as e:
        conn.rollback()
        print(f"Error creating tables: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    create_tables_manually()