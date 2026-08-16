import sqlalchemy as sa
import pytest
from sqlalchemy import inspect

from app.db.adopt_legacy_schema import (
    REVISION_0003,
    LegacySchemaError,
    adopt_legacy_schema,
)
from app.models import Base
from app.models.bar import Bar


def test_fresh_database_is_left_for_alembic() -> None:
    engine = sa.create_engine("sqlite://")
    with engine.begin() as connection:
        assert adopt_legacy_schema(connection) is None
        assert "alembic_version" not in inspect(connection).get_table_names()


def test_complete_create_all_schema_is_adopted() -> None:
    engine = sa.create_engine("sqlite://")
    with engine.begin() as connection:
        Base.metadata.create_all(connection)

        assert adopt_legacy_schema(connection) == REVISION_0003
        version = connection.execute(
            sa.text("SELECT version_num FROM alembic_version")
        ).scalar_one()
        assert version == REVISION_0003


def test_complete_schema_with_empty_version_table_is_adopted() -> None:
    engine = sa.create_engine("sqlite://")
    with engine.begin() as connection:
        Base.metadata.create_all(connection)
        connection.execute(
            sa.text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)")
        )

        assert adopt_legacy_schema(connection) == REVISION_0003
        version = connection.execute(
            sa.text("SELECT version_num FROM alembic_version")
        ).scalar_one()
        assert version == REVISION_0003


def test_partial_schema_fails_closed() -> None:
    engine = sa.create_engine("sqlite://")
    with engine.begin() as connection:
        Bar.__table__.create(connection)

        with pytest.raises(LegacySchemaError, match="partial legacy schema"):
            adopt_legacy_schema(connection)


def test_required_unknown_legacy_column_fails_closed() -> None:
    engine = sa.create_engine("sqlite://")
    with engine.begin() as connection:
        Base.metadata.create_all(connection)
        connection.execute(sa.text("ALTER TABLE bars ADD COLUMN legacy_code VARCHAR NOT NULL"))

        with pytest.raises(LegacySchemaError, match="legacy_code is NOT NULL"):
            adopt_legacy_schema(connection)


def test_nullable_unknown_legacy_column_is_safe() -> None:
    engine = sa.create_engine("sqlite://")
    with engine.begin() as connection:
        Base.metadata.create_all(connection)
        connection.execute(sa.text("ALTER TABLE bars ADD COLUMN legacy_note VARCHAR"))

        assert adopt_legacy_schema(connection) == REVISION_0003
