"""
Comprehensive test suite for SQLAlchemy models as defined in task1.md.

Tests validate:
- All required tables exist with correct columns, types, and constraints
- Foreign keys are properly defined
- Relationships are correctly configured
- Indexes exist as specified
- Enum values match CONTRACTS.md
- No models are imported outside app/repositories/
"""

import datetime as dt
from sqlalchemy import inspect, Integer, String, Float, DateTime, Enum as SQLEnum

from app.db.base import Base
from app.db.models import User, Batch, Prediction, AuditLog
from app.core.constants import BatchStatus, Role


class TestModelExistence:
    """Test that all required models exist."""

    def test_user_model_exists(self):
        assert User is not None
        assert User.__tablename__ == "users"

    def test_batch_model_exists(self):
        assert Batch is not None
        assert Batch.__tablename__ == "batches"

    def test_prediction_model_exists(self):
        assert Prediction is not None
        assert Prediction.__tablename__ == "predictions"

    def test_audit_log_model_exists(self):
        assert AuditLog is not None
        assert AuditLog.__tablename__ == "audit_logs"


class TestUserModel:
    """Validate User model structure per task1.md."""

    def test_user_has_required_columns(self):
        cols = set(User.__table__.c.keys())
        assert {"id", "email", "hashed_password", "role", "created_at"} <= cols

    def test_user_column_types(self):
        c = User.__table__.c
        assert isinstance(c.id.type, Integer)
        assert isinstance(c.email.type, String)
        assert isinstance(c.hashed_password.type, String)
        assert isinstance(c.created_at.type, DateTime)

    def test_user_constraints(self):
        c = User.__table__.c
        assert c.id.primary_key and c.id.autoincrement
        assert c.email.unique and not c.email.nullable
        assert not c.hashed_password.nullable
        assert not c.role.nullable

    def test_user_indexes(self):
        idx_names = {idx.name for idx in User.__table__.indexes}
        assert "ix_users_email" in idx_names
        assert "ix_users_role" in idx_names

    def test_user_relationships(self):
        assert hasattr(User, "audit_logs")

    def test_user_foreign_keys(self):
        assert len(list(User.__table__.foreign_keys)) == 0


class TestBatchModel:
    """Validate Batch model structure."""

    def test_batch_has_required_columns(self):
        cols = set(Batch.__table__.c.keys())
        assert {"id", "state", "created_at", "updated_at"} <= cols

    def test_batch_column_types(self):
        c = Batch.__table__.c
        assert isinstance(c.id.type, Integer)
        assert isinstance(c.created_at.type, DateTime)
        assert isinstance(c.updated_at.type, DateTime)

    def test_batch_constraints(self):
        c = Batch.__table__.c
        assert c.id.primary_key and c.id.autoincrement
        assert not c.state.nullable
        assert not c.created_at.nullable
        assert not c.updated_at.nullable

    def test_batch_indexes(self):
        idx_names = {idx.name for idx in Batch.__table__.indexes}
        assert "ix_batches_state" in idx_names
        assert "ix_batches_created_at" in idx_names

    def test_batch_relationships(self):
        assert hasattr(Batch, "predictions")

    def test_updated_at_has_onupdate(self):
        col = Batch.__table__.c.updated_at
        # onupdate is a Python callable (datetime.utcnow) - just check it's set
        assert col.onupdate is not None


class TestPredictionModel:
    """Validate Prediction model structure."""

    def test_prediction_has_required_columns(self):
        cols = set(Prediction.__table__.c.keys())
        expected = {"id", "batch_id", "label", "confidence", "overlay_path", "created_at"}
        assert expected <= cols

    def test_prediction_column_types(self):
        c = Prediction.__table__.c
        assert isinstance(c.id.type, Integer)
        assert isinstance(c.batch_id.type, Integer)
        assert isinstance(c.confidence.type, Float)
        assert isinstance(c.created_at.type, DateTime)

    def test_prediction_constraints(self):
        c = Prediction.__table__.c
        assert c.id.primary_key and c.id.autoincrement
        assert not c.batch_id.nullable
        assert not c.label.nullable
        assert not c.confidence.nullable
        assert not c.overlay_path.nullable
        assert not c.created_at.nullable

    def test_prediction_foreign_key(self):
        fks = list(Prediction.__table__.c.batch_id.foreign_keys)
        assert len(fks) == 1
        fk = fks[0]
        assert fk.column.table.name == "batches"
        assert fk.column.name == "id"
        assert fk.ondelete == "CASCADE"

    def test_prediction_indexes(self):
        idx_names = {idx.name for idx in Prediction.__table__.indexes}
        assert "ix_predictions_batch_id" in idx_names
        assert "ix_predictions_label" in idx_names
        assert "ix_predictions_confidence" in idx_names
        assert "ix_predictions_created_at" in idx_names
        assert "ix_predictions_batch_created" in idx_names

    def test_prediction_relationships(self):
        assert hasattr(Prediction, "batch")

    def test_prediction_length_constraints(self):
        c = Prediction.__table__.c
        assert c.label.type.length == 100
        assert c.overlay_path.type.length == 500


class TestAuditLogModel:
    """Validate AuditLog model structure."""

    def test_audit_log_has_required_columns(self):
        cols = set(AuditLog.__table__.c.keys())
        expected = {"id", "actor_id", "action", "target", "timestamp"}
        assert expected <= cols

    def test_audit_log_column_types(self):
        c = AuditLog.__table__.c
        assert isinstance(c.id.type, Integer)
        assert isinstance(c.actor_id.type, Integer)
        assert isinstance(c.action.type, String)
        assert isinstance(c.target.type, String)
        assert isinstance(c.timestamp.type, DateTime)

    def test_audit_log_constraints(self):
        c = AuditLog.__table__.c
        assert c.id.primary_key and c.id.autoincrement
        assert not c.actor_id.nullable
        assert not c.action.nullable
        assert not c.target.nullable
        assert not c.timestamp.nullable

    def test_audit_log_foreign_key(self):
        fks = list(AuditLog.__table__.c.actor_id.foreign_keys)
        assert len(fks) == 1
        fk = fks[0]
        assert fk.column.table.name == "users"
        assert fk.column.name == "id"
        assert fk.ondelete == "SET NULL"

    def test_audit_log_indexes(self):
        idx_names = {idx.name for idx in AuditLog.__table__.indexes}
        assert "ix_audit_logs_actor_id" in idx_names
        assert "ix_audit_logs_action" in idx_names
        assert "ix_audit_logs_timestamp" in idx_names
        assert "ix_audit_logs_actor_timestamp" in idx_names

    def test_audit_log_relationships(self):
        assert hasattr(AuditLog, "actor")

    def test_audit_log_length_constraints(self):
        c = AuditLog.__table__.c
        assert c.action.type.length == 100
        assert c.target.type.length == 500


class TestEnumIntegrity:
    """Verify enum values match CONTRACTS.md."""

    def test_batch_status_enum_values(self):
        # Values are lowercase as defined
        expected = {"pending", "processing", "complete", "failed"}
        actual = {status.value for status in BatchStatus}
        assert actual == expected

    def test_role_enum_values(self):
        expected = {"admin", "reviewer", "auditor"}
        actual = {role.value for role in Role}
        assert actual == expected


class TestCrossModelIntegrity:
    """Validate cross-model relationships and constraints."""

    def test_batch_prediction_relationship(self):
        rel = Batch.predictions.property
        # cascade includes delete-orphan
        assert "delete-orphan" in str(rel.cascade)
        # uselist true
        assert rel.uselist is True

        pred_rel = Prediction.batch.property
        assert pred_rel.uselist is False

    def test_user_audit_log_relationship(self):
        rel = User.audit_logs.property
        assert rel.uselist is True
        audit_rel = AuditLog.actor.property
        assert audit_rel.uselist is False

    def test_all_foreign_keys_valid(self):
        checks = [
            (Prediction, "batch_id", "batches", "id", "CASCADE"),
            (AuditLog, "actor_id", "users", "id", "SET NULL"),
        ]
        for model, col_name, ref_table, ref_col, ondelete in checks:
            col = model.__table__.c[col_name]
            fks = list(col.foreign_keys)
            assert len(fks) == 1, f"{model.__name__}.{col_name} missing FK"
            fk = fks[0]
            assert fk.column.table.name == ref_table
            assert fk.column.name == ref_col
            assert fk.ondelete == ondelete

    def test_all_tables_have_primary_keys(self):
        for model in [User, Batch, Prediction, AuditLog]:
            pk = model.__table__.primary_key
            assert len(pk.columns) > 0

    def test_created_at_timestamps(self):
        assert User.__table__.c.created_at.default is not None
        assert Batch.__table__.c.created_at.default is not None
        assert Batch.__table__.c.updated_at.default is not None
        assert Prediction.__table__.c.created_at.default is not None
        assert AuditLog.__table__.c.timestamp.default is not None


class TestModelIsolation:
    """Ensure models are not imported outside app/repositories/."""

    def test_models_not_imported_in_repositories_yet(self):
        import os
        here = os.path.dirname(__file__)  # tests/db
        project_root = os.path.abspath(os.path.join(here, "..", ".."))
        repo_dir = os.path.join(project_root, "app", "repositories")

        for filename in os.listdir(repo_dir):
            if filename.endswith(".py") and filename != "__init__.py":
                filepath = os.path.join(repo_dir, filename)
                with open(filepath, "r", encoding="utf-8-sig") as f:
                    content = f.read()
                stripped = content.strip()
                assert stripped.startswith("#") or stripped == "", \
                    f"Repository {filename} should be placeholder but contains code"

    def test_models_not_imported_in_services_yet(self):
        import os
        here = os.path.dirname(__file__)  # tests/db
        project_root = os.path.abspath(os.path.join(here, "..", ".."))
        service_dir = os.path.join(project_root, "app", "services")

        for filename in os.listdir(service_dir):
            if filename.endswith(".py") and filename != "__init__.py":
                filepath = os.path.join(service_dir, filename)
                with open(filepath, "r", encoding="utf-8-sig") as f:
                    content = f.read()
                stripped = content.strip()
                assert stripped.startswith("#") or stripped == "", \
                    f"Service {filename} should be placeholder but contains code"
