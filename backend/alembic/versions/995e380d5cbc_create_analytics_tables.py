"""create_analytics_tables

Revision ID: 995e380d5cbc
Revises: 77de65e4a315
Create Date: 2025-05-09 22:11:34.822849

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '995e380d5cbc'
down_revision: Union[str, None] = '77de65e4a315'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
