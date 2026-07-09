from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class RunStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    AGENT_FAILED = "agent_failed"
    TESTS_FAILED = "tests_failed"
    COMPLETED = "completed"
    COMPLETED_WITHOUT_PR = "completed_without_pr"
    PR_FAILED = "pr_failed"
    FAILED = "failed"


class RunCreateRequest(BaseModel):
    repo_url: str
    target_paths: list[str] = Field(min_length=1)
    base_branch: str = "main"
    test_framework: Literal["pytest"] = "pytest"
    create_pr: bool = False
    source_pr_number: int | None = None

    @field_validator("repo_url", "base_branch")
    @classmethod
    def require_non_empty_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("value must not be empty")
        return stripped

    @field_validator("target_paths")
    @classmethod
    def require_relative_target_paths(cls, values: list[str]) -> list[str]:
        for value in values:
            path = Path(value)
            if path.is_absolute() or ".." in path.parts:
                raise ValueError("target_paths must be relative paths inside the repo")
        return values


class RunCreateResponse(BaseModel):
    id: UUID
    status: RunStatus


class RunRecord(BaseModel):
    id: UUID
    status: RunStatus
    request: RunCreateRequest
    created_at: datetime
    updated_at: datetime
    repo_path: str | None = None
    agent_stdout: str | None = None
    agent_stderr: str | None = None
    pytest_exit_code: int | None = None
    pytest_stdout: str | None = None
    pytest_stderr: str | None = None
    generated_diff: str | None = None
    pr_url: str | None = None
    ci_status: str | None = None
    error: str | None = None
