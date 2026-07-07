import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from app.repositories import create_schema, get_session_factory

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")


@pytest.fixture
def session_factory():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    create_schema(engine)
    return get_session_factory(engine)
