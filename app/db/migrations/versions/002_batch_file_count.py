"""add file_count to batches

Revision ID: 002
Revises: 001
Create Date: 2026-05-15 00:00:00.000000

Records how many documents a batch is expected to contain. An HTTP
/batches/upload request now creates ONE batch for all uploaded files,
so the inference worker needs the expected count to know when every
file in the batch has been classified before flipping it to COMPLETE.

server_default="1" backfills existing rows (each legacy batch was
one file) and keeps the column non-null without a data migration.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "batches",
        sa.Column(
            "file_count",
            sa.Integer,
            nullable=False,
            server_default=sa.text("1"),
        ),
    )


def downgrade() -> None:
    op.drop_column("batches", "file_count")
