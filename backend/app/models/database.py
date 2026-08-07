"""
SQLAlchemy ORM models and async engine/session setup.
"""
import enum
import uuid
from datetime import datetime

from sqlalchemy import (Boolean, Column, DateTime, Enum, Float, ForeignKey,
                         Integer, String, Text, JSON)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base, relationship

from app.core.config import settings

Base = declarative_base()

engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def gen_uuid():
    return str(uuid.uuid4())


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"


class AnalysisStatus(str, enum.Enum):
    PENDING = "pending"
    UPLOADING = "uploading"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class DumpFormat(str, enum.Enum):
    RAW = "raw"
    DMP = "dmp"
    ELF = "elf"
    MACHO = "macho"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    username = Column(String(64), unique=True, nullable=False, index=True)
    email = Column(String(128), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole, values_callable=lambda x: [e.value for e in x]), default=UserRole.VIEWER, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    analyses = relationship("Analysis", back_populates="owner")
    audit_logs = relationship("AuditLog", back_populates="user")


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_hash_sha256 = Column(String(64), nullable=True, index=True)
    dump_format = Column(Enum(DumpFormat, values_callable=lambda x: [e.value for e in x]), nullable=False)
    status = Column(Enum(AnalysisStatus, values_callable=lambda x: [e.value for e in x]), default=AnalysisStatus.PENDING, nullable=False)
    progress = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    celery_task_id = Column(String(64), nullable=True)

    owner_id = Column(UUID(as_uuid=False), ForeignKey("users.id"))
    owner = relationship("User", back_populates="analyses")

    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    processes = relationship("ProcessRecord", back_populates="analysis", cascade="all, delete-orphan")
    connections = relationship("NetworkConnection", back_populates="analysis", cascade="all, delete-orphan")
    yara_matches = relationship("YaraMatch", back_populates="analysis", cascade="all, delete-orphan")
    ml_findings = relationship("MLFinding", back_populates="analysis", cascade="all, delete-orphan")


class ProcessRecord(Base):
    __tablename__ = "process_records"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    analysis_id = Column(UUID(as_uuid=False), ForeignKey("analyses.id"))
    analysis = relationship("Analysis", back_populates="processes")

    pid = Column(Integer, nullable=False)
    ppid = Column(Integer, nullable=True)
    name = Column(String(255), nullable=False)
    create_time = Column(DateTime, nullable=True)
    exit_time = Column(DateTime, nullable=True)
    threads = Column(Integer, default=0)
    handles = Column(Integer, default=0)
    cmdline = Column(Text, nullable=True)
    is_suspicious = Column(Boolean, default=False)
    suspicion_reasons = Column(JSON, nullable=True)


class NetworkConnection(Base):
    __tablename__ = "network_connections"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    analysis_id = Column(UUID(as_uuid=False), ForeignKey("analyses.id"))
    analysis = relationship("Analysis", back_populates="connections")

    pid = Column(Integer, nullable=True)
    process_name = Column(String(255), nullable=True)
    local_addr = Column(String(64), nullable=True)
    local_port = Column(Integer, nullable=True)
    remote_addr = Column(String(64), nullable=True)
    remote_port = Column(Integer, nullable=True)
    protocol = Column(String(16), nullable=True)
    state = Column(String(32), nullable=True)
    is_suspicious = Column(Boolean, default=False)


class YaraMatch(Base):
    __tablename__ = "yara_matches"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    analysis_id = Column(UUID(as_uuid=False), ForeignKey("analyses.id"))
    analysis = relationship("Analysis", back_populates="yara_matches")

    rule_name = Column(String(255), nullable=False)
    rule_namespace = Column(String(255), nullable=True)
    matched_pid = Column(Integer, nullable=True)
    offset = Column(String(32), nullable=True)
    severity = Column(String(16), default="medium")
    tags = Column(JSON, nullable=True)
    strings_matched = Column(JSON, nullable=True)


class MLFinding(Base):
    __tablename__ = "ml_findings"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    analysis_id = Column(UUID(as_uuid=False), ForeignKey("analyses.id"))
    analysis = relationship("Analysis", back_populates="ml_findings")

    entity_type = Column(String(32), nullable=False)  # process/connection
    entity_ref = Column(String(255), nullable=False)
    anomaly_score = Column(Float, nullable=False)
    is_anomaly = Column(Boolean, default=False)
    features = Column(JSON, nullable=True)
    explanation = Column(Text, nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=True)
    user = relationship("User", back_populates="audit_logs")

    action = Column(String(128), nullable=False)
    resource = Column(String(255), nullable=True)
    ip_address = Column(String(64), nullable=True)
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
