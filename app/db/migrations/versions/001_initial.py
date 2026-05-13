"""initial migration - create all tables

Revision ID: 001
Revises: 
Create Date: 2026-05-13 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all tables."""
    # Create users table
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True, index=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role", sa.Enum("admin", "reviewer", "auditor", name="role"), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_role", "users", ["role"])

    # Create batches table
    op.create_table(
        "batches",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("state", sa.Enum("pending", "processing", "complete", "failed", name="batchstatus"), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.text("now()"), onupdate=sa.text("now()")),
    )
    op.create_index("ix_batches_state", "batches", ["state"])
    op.create_index("ix_batches_created_at", "batches", ["created_at"])

    # Create predictions table
    op.create_table(
        "predictions",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("batch_id", sa.Integer, sa.ForeignKey("batches.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("label", sa.String(100), nullable=False, index=True),
        sa.Column("confidence", sa.Float, nullable=False),
        sa.Column("overlay_path", sa.String(500), nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_predictions_batch_id", "predictions", ["batch_id"])
    op.create_index("ix_predictions_label", "predictions", ["label"])
    op.create_index("ix_predictions_confidence", "predictions", ["confidence"])
    op.create_index("ix_predictions_created_at", "predictions", ["created_at"])
    op.create_index("ix_predictions_batch_created", "predictions", ["batch_id", "created_at"])

    # Create audit_logs table
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=False, index=True),
        sa.Column("action", sa.String(100), nullable=False, index=True),
        sa.Column("target", sa.String(500), nullable=False),
        sa.Column("timestamp", sa.DateTime, nullable=False, server_default=sa.text("now()"), index=True),
    )
    op.create_index("ix_audit_logs_actor_id", "audit_logs", ["actor_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_timestamp", "audit_logs", ["timestamp"])
    op.create_index("ix_audit_logs_actor_timestamp", "audit_logs", ["actor_id", "timestamp"])


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table("audit_logs")
    op.drop_table("predictions")
    op.drop_table("batches")
    op.drop_table("users")
    # Drop ENUM types
    op.execute("DROP TYPE IF EXISTS role")
    op.execute("DROP TYPE IF EXISTS batchstatus")
