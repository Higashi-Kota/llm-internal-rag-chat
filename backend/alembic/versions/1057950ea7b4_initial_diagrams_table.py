"""Initial diagrams table.

Revision ID: 1057950ea7b4
Revises:
Create Date: 2026-01-02 19:58:56.386673
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1057950ea7b4"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create diagrams table."""
    op.create_table(
        "diagrams",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("trace_id", sa.String(), nullable=False, index=True),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("language", sa.String(), nullable=False),
        sa.Column("diagram_type", sa.String(), nullable=False),
        sa.Column("mermaid_code", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("model", sa.String(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False, default=0),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )

    # Create index on created_at for efficient ordering
    op.create_index("idx_diagrams_created_at", "diagrams", ["created_at"], unique=False)


def downgrade() -> None:
    """Drop diagrams table."""
    op.drop_index("idx_diagrams_created_at", table_name="diagrams")
    op.drop_table("diagrams")
