"""create learner adaptations table

Revision ID: 20260421_0005
Revises: 20260327_0004
Create Date: 2026-04-21 00:00:05.000000
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260421_0005"
down_revision = "20260327_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "learner_adaptations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "profile_sig",
            sa.String(length=32),
            nullable=False,
            server_default="default",
        ),
        sa.Column(
            "adaptation_ctx",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "generated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("source_profile_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )


def downgrade() -> None:
    op.drop_table("learner_adaptations")
