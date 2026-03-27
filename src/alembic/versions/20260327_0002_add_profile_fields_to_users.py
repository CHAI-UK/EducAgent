"""add profile fields to users

Revision ID: 20260327_0002
Revises: 20260316_0001
Create Date: 2026-03-27 00:00:00.000000
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260327_0002"
down_revision = "20260316_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("first_name", sa.String(length=100), nullable=True))
    op.add_column("users", sa.Column("last_name", sa.String(length=100), nullable=True))
    op.add_column("users", sa.Column("institution", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("avatar_path", sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "avatar_path")
    op.drop_column("users", "institution")
    op.drop_column("users", "last_name")
    op.drop_column("users", "first_name")
