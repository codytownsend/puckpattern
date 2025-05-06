from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial schema."""
    # Create teams table
    op.create_table(
        'teams',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('team_id', sa.String(), nullable=True),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('abbreviation', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_teams_id'), 'teams', ['id'], unique=False)
    op.create_index(op.f('ix_teams_name'), 'teams', ['name'], unique=False)
    op.create_index(op.f('ix_teams_team_id'), 'teams', ['team_id'], unique=True)
    
    # Create players table
    op.create_table(
        'players',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('player_id', sa.String(), nullable=True),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('team_id', sa.Integer(), nullable=True),
        sa.Column('position', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_players_id'), 'players', ['id'], unique=False)
    op.create_index(op.f('ix_players_name'), 'players', ['name'], unique=False)
    op.create_index(op.f('ix_players_player_id'), 'players', ['player_id'], unique=True)
    
    # Create games table
    op.create_table(
        'games',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('game_id', sa.String(), nullable=True),
        sa.Column('date', sa.DateTime(), nullable=True),
        sa.Column('home_team_id', sa.Integer(), nullable=True),
        sa.Column('away_team_id', sa.Integer(), nullable=True),
        sa.Column('season', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('period', sa.Integer(), nullable=True),
        sa.Column('time_remaining', sa.String(), nullable=True),
        sa.Column('home_score', sa.Integer(), nullable=True),
        sa.Column('away_score', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['away_team_id'], ['teams.id'], ),
        sa.ForeignKeyConstraint(['home_team_id'], ['teams.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_games_game_id'), 'games', ['game_id'], unique=True)
    op.create_index(op.f('ix_games_id'), 'games', ['id'], unique=False)
    
    # Create player_game association table
    op.create_table(
        'player_game',
        sa.Column('player_id', sa.Integer(), nullable=True),
        sa.Column('game_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['game_id'], ['games.id'], ),
        sa.ForeignKeyConstraint(['player_id'], ['players.id'], )
    )
    
    # Create game_events table
    op.create_table(
        'game_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('game_id', sa.String(), nullable=True),
        sa.Column('event_type', sa.String(), nullable=True),
        sa.Column('period', sa.Integer(), nullable=True),
        sa.Column('time_elapsed', sa.Float(), nullable=True),
        sa.Column('x_coordinate', sa.Float(), nullable=True),
        sa.Column('y_coordinate', sa.Float(), nullable=True),
        sa.Column('player_id', sa.Integer(), nullable=True),
        sa.Column('team_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['player_id'], ['players.id'], ),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_game_events_event_type'), 'game_events', ['event_type'], unique=False)
    op.create_index(op.f('ix_game_events_game_id'), 'game_events', ['game_id'], unique=False)
    op.create_index(op.f('ix_game_events_id'), 'game_events', ['id'], unique=False)
    
    # Create shot_events table
    op.create_table(
        'shot_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=True),
        sa.Column('shot_type', sa.String(), nullable=True),
        sa.Column('distance', sa.Float(), nullable=True),
        sa.Column('angle', sa.Float(), nullable=True),
        sa.Column('goal', sa.Boolean(), nullable=True),
        sa.Column('xg', sa.Float(), nullable=True),
        sa.Column('shooter_id', sa.Integer(), nullable=True),
        sa.Column('goalie_id', sa.Integer(), nullable=True),
        sa.Column('primary_assist_id', sa.Integer(), nullable=True),
        sa.Column('secondary_assist_id', sa.Integer(), nullable=True),
        sa.Column('preceding_event_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['event_id'], ['game_events.id'], ),
        sa.ForeignKeyConstraint(['goalie_id'], ['players.id'], ),
        sa.ForeignKeyConstraint(['preceding_event_id'], ['game_events.id'], ),
        sa.ForeignKeyConstraint(['primary_assist_id'], ['players.id'], ),
        sa.ForeignKeyConstraint(['secondary_assist_id'], ['players.id'], ),
        sa.ForeignKeyConstraint(['shooter_id'], ['players.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_shot_events_id'), 'shot_events', ['id'], unique=False)
    
    # Create zone_entries table
    op.create_table(
        'zone_entries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=True),
        sa.Column('entry_type', sa.String(), nullable=True),
        sa.Column('controlled', sa.Boolean(), nullable=True),
        sa.Column('player_id', sa.Integer(), nullable=True),
        sa.Column('defender_id', sa.Integer(), nullable=True),
        sa.Column('lead_to_shot', sa.Boolean(), default=False, nullable=True),
        sa.Column('lead_to_shot_time', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['event_id'], ['game_events.id'], ),
        sa.ForeignKeyConstraint(['player_id'], ['players.id'], ),
        sa.ForeignKeyConstraint(['defender_id'], ['players.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_zone_entries_id'), 'zone_entries', ['id'], unique=False)
    
    # Create passes table
    op.create_table(
        'passes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=True),
        sa.Column('passer_id', sa.Integer(), nullable=True),
        sa.Column('recipient_id', sa.Integer(), nullable=True),
        sa.Column('pass_type', sa.String(), nullable=True),
        sa.Column('zone', sa.String(), nullable=True),
        sa.Column('completed', sa.Boolean(), nullable=True),
        sa.Column('intercepted', sa.Boolean(), default=False, nullable=True),
        sa.Column('intercepted_by_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['event_id'], ['game_events.id'], ),
        sa.ForeignKeyConstraint(['passer_id'], ['players.id'], ),
        sa.ForeignKeyConstraint(['recipient_id'], ['players.id'], ),
        sa.ForeignKeyConstraint(['intercepted_by_id'], ['players.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_passes_id'), 'passes', ['id'], unique=False)
    
    # Create puck_recoveries table
    op.create_table(
        'puck_recoveries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=True),
        sa.Column('player_id', sa.Integer(), nullable=True),
        sa.Column('zone', sa.String(), nullable=True),
        sa.Column('recovery_type', sa.String(), nullable=True),
        sa.Column('lead_to_possession', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['event_id'], ['game_events.id'], ),
        sa.ForeignKeyConstraint(['player_id'], ['players.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_puck_recoveries_id'), 'puck_recoveries', ['id'], unique=False)
    
    # Create shifts table
    op.create_table(
        'shifts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('game_id', sa.Integer(), nullable=True),
        sa.Column('player_id', sa.Integer(), nullable=True),
        sa.Column('start_time', sa.Float(), nullable=True),
        sa.Column('end_time', sa.Float(), nullable=True),
        sa.Column('period', sa.Integer(), nullable=True),
        sa.Column('team_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['game_id'], ['games.id'], ),
        sa.ForeignKeyConstraint(['player_id'], ['players.id'], ),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_shifts_id'), 'shifts', ['id'], unique=False)
    
    # Create power_plays table
    op.create_table(
        'power_plays',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('game_id', sa.Integer(), nullable=True),
        sa.Column('team_id', sa.Integer(), nullable=True),
        sa.Column('start_time', sa.Float(), nullable=True),
        sa.Column('end_time', sa.Float(), nullable=True),
        sa.Column('period', sa.Integer(), nullable=True),
        sa.Column('duration', sa.Float(), nullable=True),
        sa.Column('advantage_type', sa.String(), nullable=True),
        sa.Column('successful', sa.Boolean(), nullable=True),
        sa.Column('formation', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['game_id'], ['games.id'], ),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_power_plays_id'), 'power_plays', ['id'], unique=False)
    
    # Create player_game_stats table
    op.create_table(
        'player_game_stats',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('player_id', sa.Integer(), nullable=True),
        sa.Column('game_id', sa.Integer(), nullable=True),
        sa.Column('team_id', sa.Integer(), nullable=True),
        sa.Column('toi', sa.Float(), nullable=True),
        sa.Column('goals', sa.Integer(), default=0, nullable=True),
        sa.Column('assists', sa.Integer(), default=0, nullable=True),
        sa.Column('shots', sa.Integer(), default=0, nullable=True),
        sa.Column('hits', sa.Integer(), default=0, nullable=True),
        sa.Column('blocks', sa.Integer(), default=0, nullable=True),
        sa.Column('pim', sa.Integer(), default=0, nullable=True),
        sa.Column('xg', sa.Float(), default=0.0, nullable=True),
        sa.Column('xg_against', sa.Float(), default=0.0, nullable=True),
        sa.Column('corsi_for', sa.Integer(), default=0, nullable=True),
        sa.Column('corsi_against', sa.Integer(), default=0, nullable=True),
        sa.Column('zone_starts_off', sa.Integer(), default=0, nullable=True),
        sa.Column('zone_starts_def', sa.Integer(), default=0, nullable=True),
        sa.Column('zone_starts_neutral', sa.Integer(), default=0, nullable=True),
        sa.Column('ecr', sa.Float(), nullable=True),
        sa.Column('pri', sa.Float(), nullable=True),
        sa.Column('pdi', sa.Float(), nullable=True),
        sa.Column('xg_delta_psm', sa.Float(), nullable=True),
        sa.Column('sfs', sa.Float(), nullable=True),
        sa.Column('omc', sa.Float(), nullable=True),
        sa.Column('ice_plus', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['game_id'], ['games.id'], ),
        sa.ForeignKeyConstraint(['player_id'], ['players.id'], ),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_player_game_stats_id'), 'player_game_stats', ['id'], unique=False)
    
    # Create team_game_stats table
    op.create_table(
        'team_game_stats',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=True),
        sa.Column('game_id', sa.Integer(), nullable=True),
        sa.Column('goals', sa.Integer(), default=0, nullable=True),
        sa.Column('shots', sa.Integer(), default=0, nullable=True),
        sa.Column('hits', sa.Integer(), default=0, nullable=True),
        sa.Column('blocks', sa.Integer(), default=0, nullable=True),
        sa.Column('pim', sa.Integer(), default=0, nullable=True),
        sa.Column('faceoff_wins', sa.Integer(), default=0, nullable=True),
        sa.Column('faceoff_losses', sa.Integer(), default=0, nullable=True),
        sa.Column('xg', sa.Float(), default=0.0, nullable=True),
        sa.Column('xg_against', sa.Float(), default=0.0, nullable=True),
        sa.Column('corsi_for', sa.Integer(), default=0, nullable=True),
        sa.Column('corsi_against', sa.Integer(), default=0, nullable=True),
        sa.Column('forecheck_style', sa.String(), nullable=True),
        sa.Column('defensive_structure', sa.String(), nullable=True),
        sa.Column('pp_formation', sa.String(), nullable=True),
        sa.Column('pk_formation', sa.String(), nullable=True),
        sa.Column('team_ecr', sa.Float(), nullable=True),
        sa.Column('team_pri', sa.Float(), nullable=True),
        sa.Column('team_pdi', sa.Float(), nullable=True),
        sa.Column('system_metrics', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['game_id'], ['games.id'], ),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_team_game_stats_id'), 'team_game_stats', ['id'], unique=False)
    
    # Create team_profiles table
    op.create_table(
        'team_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=True),
        sa.Column('season', sa.String(), nullable=True),
        sa.Column('offensive_style', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('defensive_style', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('special_teams', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('team_fingerprint', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('similar_teams', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_team_profiles_id'), 'team_profiles', ['id'], unique=False)
    
    # Create player_profiles table
    op.create_table(
        'player_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('player_id', sa.Integer(), nullable=True),
        sa.Column('season', sa.String(), nullable=True),
        sa.Column('primary_role', sa.String(), nullable=True),
        sa.Column('secondary_role', sa.String(), nullable=True),
        sa.Column('offensive_behavior', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('defensive_behavior', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('transition_behavior', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('current_team_fit', sa.Float(), nullable=True),
        sa.Column('optimal_system_type', sa.String(), nullable=True),
        sa.Column('system_fit_scores', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('season_ice_plus', sa.Float(), nullable=True),
        sa.Column('consistency_metrics', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['player_id'], ['players.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_player_profiles_id'), 'player_profiles', ['id'], unique=False)


def downgrade() -> None:
    """Revert schema changes."""
    # Drop player_profiles table
    op.drop_index(op.f('ix_player_profiles_id'), table_name='player_profiles')
    op.drop_table('player_profiles')
    
    # Drop team_profiles table
    op.drop_index(op.f('ix_team_profiles_id'), table_name='team_profiles')
    op.drop_table('team_profiles')
    
    # Drop team_game_stats table
    op.drop_index(op.f('ix_team_game_stats_id'), table_name='team_game_stats')
    op.drop_table('team_game_stats')
    
    # Drop player_game_stats table
    op.drop_index(op.f('ix_player_game_stats_id'), table_name='player_game_stats')
    op.drop_table('player_game_stats')
    
    # Drop power_plays table
    op.drop_index(op.f('ix_power_plays_id'), table_name='power_plays')
    op.drop_table('power_plays')
    
    # Drop shifts table
    op.drop_index(op.f('ix_shifts_id'), table_name='shifts')
    op.drop_table('shifts')
    
    # Drop puck_recoveries table
    op.drop_index(op.f('ix_puck_recoveries_id'), table_name='puck_recoveries')
    op.drop_table('puck_recoveries')
    
    # Drop passes table
    op.drop_index(op.f('ix_passes_id'), table_name='passes')
    op.drop_table('passes')
    
    # Drop zone_entries table
    op.drop_index(op.f('ix_zone_entries_id'), table_name='zone_entries')
    op.drop_table('zone_entries')
    
    # Drop shot_events table
    op.drop_index(op.f('ix_shot_events_id'), table_name='shot_events')
    op.drop_table('shot_events')
    
    # Drop game_events table
    op.drop_index(op.f('ix_game_events_id'), table_name='game_events')
    op.drop_index(op.f('ix_game_events_game_id'), table_name='game_events')
    op.drop_index(op.f('ix_game_events_event_type'), table_name='game_events')
    op.drop_table('game_events')
    
    # Drop player_game association table
    op.drop_table('player_game')
    
    # Drop games table
    op.drop_index(op.f('ix_games_id'), table_name='games')
    op.drop_index(op.f('ix_games_game_id'), table_name='games')
    op.drop_table('games')
    
    # Drop players table
    op.drop_index(op.f('ix_players_player_id'), table_name='players')
    op.drop_index(op.f('ix_players_name'), table_name='players')
    op.drop_index(op.f('ix_players_id'), table_name='players')
    op.drop_table('players')
    
    # Drop teams table
    op.drop_index(op.f('ix_teams_team_id'), table_name='teams')
    op.drop_index(op.f('ix_teams_name'), table_name='teams')
    op.drop_index(op.f('ix_teams_id'), table_name='teams')
    op.drop_table('teams')