from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, Integer, String, Text, create_engine, inspect, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from app.models import RunCreateRequest, RunRecord, RunStatus


class Base(DeclarativeBase):
    pass


class RunRow(Base):
    __tablename__ = "runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    request_payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    repo_path: Mapped[str | None] = mapped_column(Text)
    agent_stdout: Mapped[str | None] = mapped_column(Text)
    agent_stderr: Mapped[str | None] = mapped_column(Text)
    pytest_exit_code: Mapped[int | None] = mapped_column(Integer)
    pytest_stdout: Mapped[str | None] = mapped_column(Text)
    pytest_stderr: Mapped[str | None] = mapped_column(Text)
    generated_diff: Mapped[str | None] = mapped_column(Text)
    pr_url: Mapped[str | None] = mapped_column(Text)
    ci_status: Mapped[str | None] = mapped_column(Text)
    error: Mapped[str | None] = mapped_column(Text)


def create_engine_from_url(database_url: str) -> Engine:
    return create_engine(database_url, future=True)


def create_schema(engine: Engine) -> None:
    Base.metadata.create_all(engine)
    _add_missing_run_columns(engine)


def _add_missing_run_columns(engine: Engine) -> None:
    inspector = inspect(engine)
    if "runs" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("runs")}
    with engine.begin() as connection:
        for column in RunRow.__table__.columns:
            if column.name in existing_columns:
                continue
            column_type = column.type.compile(dialect=connection.dialect)
            nullable = "" if column.nullable else " NOT NULL"
            connection.exec_driver_sql(f"ALTER TABLE runs ADD COLUMN {column.name} {column_type}{nullable}")


def get_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False, future=True)


class RunRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def create_run(self, request: RunCreateRequest) -> RunRecord:
        now = datetime.now(UTC)
        row = RunRow(
            id=str(uuid4()),
            status=RunStatus.QUEUED.value,
            request_payload=request.model_dump(mode="json"),
            created_at=now,
            updated_at=now,
        )
        with self._session_factory() as session:
            session.add(row)
            session.commit()
            session.refresh(row)
            return self._to_record(row)

    def get_run(self, run_id: UUID) -> RunRecord | None:
        with self._session_factory() as session:
            row = session.get(RunRow, str(run_id))
            return self._to_record(row) if row is not None else None

    def list_runs(self, limit: int = 50) -> list[RunRecord]:
        with self._session_factory() as session:
            rows = session.scalars(select(RunRow).order_by(RunRow.created_at.desc()).limit(limit)).all()
            return [self._to_record(row) for row in rows]

    def update_run(self, run_id: UUID, **fields: object) -> RunRecord:
        with self._session_factory() as session:
            row = session.get(RunRow, str(run_id))
            if row is None:
                raise KeyError(f"run not found: {run_id}")
            for key, value in fields.items():
                if key == "status" and isinstance(value, RunStatus):
                    value = value.value
                if not hasattr(row, key):
                    raise ValueError(f"unknown run field: {key}")
                setattr(row, key, value)
            row.updated_at = datetime.now(UTC)
            session.commit()
            session.refresh(row)
            return self._to_record(row)

    def _to_record(self, row: RunRow) -> RunRecord:
        return RunRecord(
            id=UUID(row.id),
            status=RunStatus(row.status),
            request=RunCreateRequest.model_validate(row.request_payload),
            created_at=row.created_at,
            updated_at=row.updated_at,
            repo_path=row.repo_path,
            agent_stdout=row.agent_stdout,
            agent_stderr=row.agent_stderr,
            pytest_exit_code=row.pytest_exit_code,
            pytest_stdout=row.pytest_stdout,
            pytest_stderr=row.pytest_stderr,
            generated_diff=row.generated_diff,
            pr_url=row.pr_url,
            ci_status=row.ci_status,
            error=row.error,
        )
