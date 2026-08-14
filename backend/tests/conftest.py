from collections.abc import Generator

import httpx
import pytest
from sqlalchemy.orm import Session, sessionmaker

from backend.app.main import app
from backend.app.persistence import models  # noqa: F401
from backend.app.persistence.base import Base
from backend.app.persistence.database import create_database_engine, get_session


@pytest.fixture
def session_factory(tmp_path) -> Generator[sessionmaker[Session]]:
    database_path = tmp_path / "test.db"
    engine = create_database_engine(f"sqlite:///{database_path.as_posix()}")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    yield factory
    engine.dispose()


@pytest.fixture
def asgi_transport(
    session_factory: sessionmaker[Session],
) -> Generator[httpx.ASGITransport]:
    def override_session() -> Generator[Session]:
        with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    yield httpx.ASGITransport(app=app)
    app.dependency_overrides.clear()
