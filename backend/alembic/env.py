from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Import models to ensure they are seen by Alembic
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.models.base import Base
from app.models.analytics import Game, ShotEvent, ZoneEntry, Pass, PuckRecovery
from app.models.analytics import Shift, PowerPlay, PlayerGameStats, TeamGameStats
from app.models.analytics import TeamProfile, PlayerProfile

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata