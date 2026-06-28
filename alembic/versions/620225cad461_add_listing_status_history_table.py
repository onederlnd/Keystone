"""add listing_status_history table

Revision ID: 620225cad461
Revises: f45831409fcc
Create Date: 2026-06-28 18:24:16.098405

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "620225cad461"
down_revision: Union[str, Sequence[str], None] = "e768cb4fb663"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
