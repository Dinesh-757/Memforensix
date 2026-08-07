"""
Pydantic request/response schemas.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.models.database import AnalysisStatus, DumpFormat, UserRole


# ---------- Auth ----------
class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    email: EmailStr
    password: str = Field(min_length=8)
    role: UserRole = UserRole.VIEWER


class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    username: str
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str
    role: str
    exp: int


# ---------- Analysis ----------
class AnalysisCreate(BaseModel):
    filename: str
    dump_format: DumpFormat


class AnalysisOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    filename: str
    file_size: int
    file_hash_sha256: Optional[str]
    dump_format: DumpFormat
    status: AnalysisStatus
    progress: int
    error_message: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]


class AnalysisListOut(BaseModel):
    total: int
    items: List[AnalysisOut]


class ProcessOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    pid: int
    ppid: Optional[int]
    name: str
    create_time: Optional[datetime]
    threads: int
    handles: int
    cmdline: Optional[str]
    is_suspicious: bool
    suspicion_reasons: Optional[List[str]]


class NetworkConnectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    pid: Optional[int]
    process_name: Optional[str]
    local_addr: Optional[str]
    local_port: Optional[int]
    remote_addr: Optional[str]
    remote_port: Optional[int]
    protocol: Optional[str]
    state: Optional[str]
    is_suspicious: bool


class YaraMatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    rule_name: str
    rule_namespace: Optional[str]
    matched_pid: Optional[int]
    offset: Optional[str]
    severity: str
    tags: Optional[List[str]]
    strings_matched: Optional[List[str]]


class MLFindingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str
    entity_ref: str
    anomaly_score: float
    is_anomaly: bool
    features: Optional[Dict[str, Any]]
    explanation: Optional[str]


class AnalysisResultsOut(BaseModel):
    analysis: AnalysisOut
    processes: List[ProcessOut]
    connections: List[NetworkConnectionOut]
    yara_matches: List[YaraMatchOut]
    ml_findings: List[MLFindingOut]
    summary: Dict[str, Any]


class WSProgressMessage(BaseModel):
    analysis_id: str
    status: AnalysisStatus
    progress: int
    stage: str
    message: str
