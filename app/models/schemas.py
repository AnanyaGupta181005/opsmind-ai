"""Pydantic contracts shared by API, agent tools and UI."""
from datetime import date, datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, EmailStr, Field


# --------------------------------------------------------------- employees
class Role(str, Enum):
    intern = "intern"
    engineer = "engineer"
    manager = "manager"
    admin = "admin"


class EmployeeIn(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    email: EmailStr
    role: Role = Role.intern
    department: str = "unassigned"
    joined_on: date
    manager_email: EmailStr | None = None
    active: bool = True


class Employee(EmployeeIn):
    id: str


class EmployeeQuery(BaseModel):
    """Structured form of a natural-language people query."""
    role: Role | None = None
    department: str | None = None
    joined_after: date | None = None
    joined_before: date | None = None
    active: bool | None = None
    limit: int = Field(default=25, ge=1, le=200)


class EmployeeUpdate(BaseModel):
    """Partial edit used by the console's Team page (role, team, active state)."""
    role: Role | None = None
    department: str | None = None
    active: bool | None = None


# --------------------------------------------------------------- documents
class DocKind(str, Enum):
    policy = "policy"
    sop = "sop"
    invoice = "invoice"
    resume = "resume"
    other = "other"


class DocumentMeta(BaseModel):
    id: str
    title: str
    kind: DocKind
    pages: int = 1
    chunks: int = 0
    uploaded_at: datetime
    indexed: bool = False
    source: str = "upload"


class ExtractedInvoice(BaseModel):
    vendor: str | None = None
    invoice_number: str | None = None
    issued_on: date | None = None
    total: float | None = None
    currency: str = "INR"
    line_items: list[dict[str, Any]] = []


class ExtractedResume(BaseModel):
    name: str | None = None
    email: str | None = None
    years_experience: float | None = None
    skills: list[str] = []
    education: list[str] = []


# --------------------------------------------------------------- rag
class Citation(BaseModel):
    doc_id: str
    title: str
    chunk_index: int
    score: float
    snippet: str


class RagAnswer(BaseModel):
    question: str
    answer: str
    citations: list[Citation]
    grounded: bool
    latency_ms: int


# --------------------------------------------------------------- agent
class ToolCall(BaseModel):
    name: str
    args: dict[str, Any] = {}
    result_summary: str | None = None
    ok: bool = True
    duration_ms: int = 0


class ChatTurn(BaseModel):
    role: Literal["user", "agent"]
    content: str
    tool_calls: list[ToolCall] = []
    citations: list[Citation] = []
    created_at: datetime


class ChatRequest(BaseModel):
    session_id: str = "default"
    message: str = Field(min_length=1, max_length=4000)
    allow_writes: bool = False


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    tool_calls: list[ToolCall] = []
    citations: list[Citation] = []
    latency_ms: int
    mode: Literal["live", "mock"] = "live"


# --------------------------------------------------------------- tasks
class TaskState(str, Enum):
    queued = "queued"
    running = "running"
    done = "done"
    failed = "failed"


class TaskRecord(BaseModel):
    id: str
    kind: str
    state: TaskState
    submitted_at: datetime
    finished_at: datetime | None = None
    detail: str | None = None
    result: dict[str, Any] | None = None
