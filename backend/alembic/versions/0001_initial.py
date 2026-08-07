"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-07-29
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    user_role = postgresql.ENUM("admin", "analyst", "viewer", name="userrole")
    analysis_status = postgresql.ENUM("pending", "uploading", "queued", "running", "completed", "failed",
                                       name="analysisstatus")
    dump_format = postgresql.ENUM("raw", "dmp", "elf", "macho", name="dumpformat")

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("username", sa.String(64), unique=True, nullable=False),
        sa.Column("email", sa.String(128), unique=True, nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime),
        sa.Column("last_login", sa.DateTime, nullable=True),
    )

    op.create_table(
        "analyses",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("file_path", sa.String(512), nullable=False),
        sa.Column("file_size", sa.Integer, nullable=False),
        sa.Column("file_hash_sha256", sa.String(64), nullable=True),
        sa.Column("dump_format", dump_format, nullable=False),
        sa.Column("status", analysis_status, nullable=False),
        sa.Column("progress", sa.Integer, default=0),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("celery_task_id", sa.String(64), nullable=True),
        sa.Column("owner_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime),
        sa.Column("started_at", sa.DateTime, nullable=True),
        sa.Column("completed_at", sa.DateTime, nullable=True),
    )

    op.create_table(
        "process_records",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("analysis_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("analyses.id")),
        sa.Column("pid", sa.Integer, nullable=False),
        sa.Column("ppid", sa.Integer, nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("create_time", sa.DateTime, nullable=True),
        sa.Column("exit_time", sa.DateTime, nullable=True),
        sa.Column("threads", sa.Integer, default=0),
        sa.Column("handles", sa.Integer, default=0),
        sa.Column("cmdline", sa.Text, nullable=True),
        sa.Column("is_suspicious", sa.Boolean, default=False),
        sa.Column("suspicion_reasons", sa.JSON, nullable=True),
    )

    op.create_table(
        "network_connections",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("analysis_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("analyses.id")),
        sa.Column("pid", sa.Integer, nullable=True),
        sa.Column("process_name", sa.String(255), nullable=True),
        sa.Column("local_addr", sa.String(64), nullable=True),
        sa.Column("local_port", sa.Integer, nullable=True),
        sa.Column("remote_addr", sa.String(64), nullable=True),
        sa.Column("remote_port", sa.Integer, nullable=True),
        sa.Column("protocol", sa.String(16), nullable=True),
        sa.Column("state", sa.String(32), nullable=True),
        sa.Column("is_suspicious", sa.Boolean, default=False),
    )

    op.create_table(
        "yara_matches",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("analysis_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("analyses.id")),
        sa.Column("rule_name", sa.String(255), nullable=False),
        sa.Column("rule_namespace", sa.String(255), nullable=True),
        sa.Column("matched_pid", sa.Integer, nullable=True),
        sa.Column("offset", sa.String(32), nullable=True),
        sa.Column("severity", sa.String(16), default="medium"),
        sa.Column("tags", sa.JSON, nullable=True),
        sa.Column("strings_matched", sa.JSON, nullable=True),
    )

    op.create_table(
        "ml_findings",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("analysis_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("analyses.id")),
        sa.Column("entity_type", sa.String(32), nullable=False),
        sa.Column("entity_ref", sa.String(255), nullable=False),
        sa.Column("anomaly_score", sa.Float, nullable=False),
        sa.Column("is_anomaly", sa.Boolean, default=False),
        sa.Column("features", sa.JSON, nullable=True),
        sa.Column("explanation", sa.Text, nullable=True),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("action", sa.String(128), nullable=False),
        sa.Column("resource", sa.String(255), nullable=True),
        sa.Column("ip_address", sa.String(64), nullable=True),
        sa.Column("details", sa.JSON, nullable=True),
        sa.Column("timestamp", sa.DateTime),
    )


def downgrade():
    op.drop_table("audit_logs")
    op.drop_table("ml_findings")
    op.drop_table("yara_matches")
    op.drop_table("network_connections")
    op.drop_table("process_records")
    op.drop_table("analyses")
    op.drop_table("users")
    sa.Enum(name="userrole").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="analysisstatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="dumpformat").drop(op.get_bind(), checkfirst=True)
