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
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(320), nullable=False, unique=True, index=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("is_superuser", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("is_verified", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("role", sa.Enum("admin", "reviewer", "auditor", name="role"), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    # Indices for columns without inline index=True
    # (email, role have index=True inline; created_at needs explicit index)
    op.create_index("ix_users_created_at", "users", ["created_at"])

    # Create batches table
    op.create_table(
        "batches",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("state", sa.Enum("pending", "processing", "complete", "failed", name="batchstatus"), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP"), onupdate=sa.text("CURRENT_TIMESTAMP")),
    )
    # Indices for columns without inline index=True
    # (state has index=True inline; created_at needs explicit index)
    op.create_index("ix_batches_created_at", "batches", ["created_at"])

    # Create predictions table
    op.create_table(
        "predictions",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("batch_id", sa.Integer, sa.ForeignKey("batches.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("label", sa.String(100), nullable=False, index=True),
        sa.Column("confidence", sa.Float, nullable=False),
        sa.Column("overlay_path", sa.String(500), nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    # Indices for columns without inline index=True
    # (batch_id, label have index=True inline)
    op.create_index("ix_predictions_confidence", "predictions", ["confidence"])
    op.create_index("ix_predictions_created_at", "predictions", ["created_at"])
    op.create_index("ix_predictions_batch_created", "predictions", ["batch_id", "created_at"])

    # Create audit_logs table
    # Drop enum if it exists from a previous failed migration (idempotency)
    op.execute("DROP TYPE IF EXISTS auditaction")
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("actor_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=False, index=True),
        sa.Column(
            "action",
            sa.Enum("change_role", "relabel_pred", "change_state", name="auditaction"),
            nullable=False,
            index=True,
        ),
        sa.Column("target_type", sa.String(50), nullable=False),
        sa.Column("target_id", sa.Integer, nullable=False),
        sa.Column("old_value", postgresql.JSONB, nullable=True),
        sa.Column("new_value", postgresql.JSONB, nullable=True),
        sa.Column("timestamp", sa.DateTime, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP"), index=True),
    )
    # Indices for columns without inline index=True
    # (actor_id, action, timestamp have index=True inline)
    # Explicit composite indices:
    op.create_index("ix_audit_logs_actor_timestamp", "audit_logs", ["actor_id", "timestamp"])
    op.create_index("ix_audit_logs_target", "audit_logs", ["target_type", "target_id"])


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table("audit_logs")
    op.drop_table("predictions")
    op.drop_table("batches")
    op.drop_table("users")
    # Drop ENUM types
    op.execute("DROP TYPE IF EXISTS auditaction")
    op.execute("DROP TYPE IF EXISTS role")
    op.execute("DROP TYPE IF EXISTS batchstatus")
