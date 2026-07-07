import pytest
from sqlalchemy import create_engine

from app.repositories import create_schema, get_session_factory


@pytest.fixture
def session_factory():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_schema(engine)
    return get_session_factory(engine)
