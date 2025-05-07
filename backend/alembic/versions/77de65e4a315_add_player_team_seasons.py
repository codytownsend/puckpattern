"""add_player_team_seasons

Revision ID: 77de65e4a315
Revises: b26135fd9410
Create Date: 2025-05-07 13:47:50.810921

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '77de65e4a315'
down_revision: Union[str, None] = 'b26135fd9410'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
