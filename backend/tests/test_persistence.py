from sqlalchemy import inspect

from backend.app.persistence import models  # noqa: F401
from backend.app.persistence.base import Base
from backend.app.persistence.database import create_database_engine


def test_sqlalchemy_metadata_can_initialize_sqlite() -> None:
    test_engine = create_database_engine("sqlite://")

    Base.metadata.create_all(test_engine)

    assert inspect(test_engine).get_table_names() == ["campaigns", "turn_snapshots"]
