"""add updated_at to users

Revision ID: 20260327_0004
Revises: 20260327_0003
Create Date: 2026-03-27 00:00:02.000000
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260327_0004"
down_revision = "20260327_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=True,
            server_default=sa.func.now(),
        ),
    )
    op.execute("UPDATE users SET updated_at = created_at WHERE updated_at IS NULL")
    op.alter_column("users", "updated_at", nullable=False)


def downgrade() -> None:
    op.drop_column("users", "updated_at")
