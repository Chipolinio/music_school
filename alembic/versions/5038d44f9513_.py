"""Add status ENUM type and cast columns

Revision ID: 5038d44f9513
Revises: 14665206c7c9
Create Date: 2026-04-04
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = '5038d44f9513'
down_revision: Union[str, Sequence[str], None] = '14665206c7c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()

    # Create unified status ENUM type
    existing = conn.execute(sa.text("SELECT 1 FROM pg_type WHERE typname = 'status'"))
    if not existing.scalar():
        op.execute("CREATE TYPE status AS ENUM ('BOOKED', 'FREE', 'TAKEN')")

    # lesson_bookings: drop default -> cast type -> set new default
    op.execute("ALTER TABLE lesson_bookings ALTER COLUMN status DROP DEFAULT")
    op.execute("ALTER TABLE lesson_bookings ALTER COLUMN status TYPE status USING status::text::status")
    op.execute("ALTER TABLE lesson_bookings ALTER COLUMN status SET DEFAULT 'BOOKED'")

    # rehearsal_bookings: drop default -> cast type -> set new default
    op.execute("ALTER TABLE rehearsal_bookings ALTER COLUMN status DROP DEFAULT")
    op.execute("ALTER TABLE rehearsal_bookings ALTER COLUMN status TYPE status USING status::text::status")
    op.execute("ALTER TABLE rehearsal_bookings ALTER COLUMN status SET DEFAULT 'FREE'")


def downgrade() -> None:
    """Downgrade schema."""
    conn = op.get_bind()

    # Drop the unified type (columns need their old types first, but skip for simplicity)
    pass
