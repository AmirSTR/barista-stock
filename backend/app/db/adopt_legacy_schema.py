"""Safely attach legacy databases to the Alembic migration history.

Older deployments created model tables with ``Base.metadata.create_all`` after
silencing an Alembic error.  Such a database is usable, but has an empty (or
missing) ``alembic_version`` table, so a later ``alembic upgrade`` tries to
create the tables again.  This module stamps only a schema that can be proven
compatible; partial or incompatible schemas fail closed.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import sqlalchemy as sa
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import inspect
from sqlalchemy.engine import Connection

from app.core.database import engine
from app.models import Base


APPLICATION_TABLES = frozenset(Base.metadata.tables)
ALEMBIC_VERSION_TABLE = "alembic_version"
REVISION_0001 = "0001_initial_schema"
REVISION_0002 = "0002_add_invoice_number"
REVISION_0003 = "0003_add_bar_chat_id"


class LegacySchemaError(RuntimeError):
    """Raised when an unversioned database cannot be adopted safely."""


def _foreign_keys(table: sa.Table) -> set[tuple[tuple[str, ...], str, tuple[str, ...], str]]:
    return {
        (
            tuple(element.parent.name for element in constraint.elements),
            constraint.referred_table.name,
            tuple(element.column.name for element in constraint.elements),
            (constraint.ondelete or "").upper(),
        )
        for constraint in table.foreign_key_constraints
    }


def _actual_foreign_keys(
    inspector, table_name: str
) -> set[tuple[tuple[str, ...], str, tuple[str, ...], str]]:
    result = set()
    for constraint in inspector.get_foreign_keys(table_name):
        options = constraint.get("options") or {}
        result.add(
            (
                tuple(constraint.get("constrained_columns") or ()),
                constraint.get("referred_table") or "",
                tuple(constraint.get("referred_columns") or ()),
                (options.get("ondelete") or "").upper(),
            )
        )
    return result


def _choose_revision(inspector) -> tuple[str, set[tuple[str, str]]]:
    bars_columns = {column["name"] for column in inspector.get_columns("bars")}
    invoice_columns = {column["name"] for column in inspector.get_columns("supply_invoices")}
    has_chat_id = "telegram_chat_id" in bars_columns
    has_invoice_number = "invoice_number" in invoice_columns

    if has_chat_id and has_invoice_number:
        return REVISION_0003, set()
    if has_invoice_number:
        return REVISION_0002, {("bars", "telegram_chat_id")}

    missing = {("supply_invoices", "invoice_number")}
    if not has_chat_id:
        missing.add(("bars", "telegram_chat_id"))
    return REVISION_0001, missing


def _validate_table(inspector, table: sa.Table, allowed_missing: set[tuple[str, str]]) -> list[str]:
    problems: list[str] = []
    actual_columns = {column["name"]: column for column in inspector.get_columns(table.name)}
    expected_columns = {column.name: column for column in table.columns}

    for column_name, expected in expected_columns.items():
        if (table.name, column_name) in allowed_missing:
            continue
        actual = actual_columns.get(column_name)
        if actual is None:
            problems.append(f"{table.name}.{column_name} is missing")
            continue
        if not expected.type._compare_type_affinity(actual["type"]):
            problems.append(
                f"{table.name}.{column_name} has type {actual['type']}, expected {expected.type}"
            )
        if bool(actual.get("nullable", True)) != bool(expected.nullable):
            problems.append(
                f"{table.name}.{column_name} nullable={actual.get('nullable')}, "
                f"expected {expected.nullable}"
            )

    for column_name, actual in actual_columns.items():
        if column_name in expected_columns:
            continue
        # Benign legacy columns are allowed, but a required column without a
        # database default would make normal model inserts fail.
        if not actual.get("nullable", True) and actual.get("default") is None:
            problems.append(
                f"legacy column {table.name}.{column_name} is NOT NULL and has no server default"
            )

    expected_pk = tuple(column.name for column in table.primary_key.columns)
    actual_pk = tuple(
        (inspector.get_pk_constraint(table.name) or {}).get("constrained_columns") or ()
    )
    if actual_pk != expected_pk:
        problems.append(f"{table.name} primary key is {actual_pk}, expected {expected_pk}")

    missing_fks = _foreign_keys(table) - _actual_foreign_keys(inspector, table.name)
    if missing_fks:
        problems.append(f"{table.name} is missing foreign keys: {sorted(missing_fks)!r}")

    # Only unique indexes are correctness-critical. Missing ordinary indexes
    # affect performance but do not make stamping the historical schema unsafe.
    actual_indexes = {
        (tuple(index.get("column_names") or ()), bool(index.get("unique")))
        for index in inspector.get_indexes(table.name)
    }
    expected_unique_indexes = {
        (tuple(column.name for column in index.columns), True)
        for index in table.indexes
        if index.unique
        and not any((table.name, column.name) in allowed_missing for column in index.columns)
    }
    missing_unique_indexes = expected_unique_indexes - actual_indexes
    if missing_unique_indexes:
        problems.append(
            f"{table.name} is missing unique indexes: {sorted(missing_unique_indexes)!r}"
        )

    return problems


def adopt_legacy_schema(connection: Connection) -> str | None:
    """Stamp a proven legacy schema and return the adopted revision.

    ``None`` means the database is fresh or already versioned and normal
    Alembic processing should continue without intervention.
    """

    inspector = inspect(connection)
    tables = set(inspector.get_table_names())

    if ALEMBIC_VERSION_TABLE in tables:
        versions = connection.execute(
            sa.text(f'SELECT version_num FROM "{ALEMBIC_VERSION_TABLE}"')
        ).scalars().all()
        if versions:
            return None

    present_application_tables = tables & APPLICATION_TABLES
    if not present_application_tables:
        return None
    if present_application_tables != APPLICATION_TABLES:
        missing = sorted(APPLICATION_TABLES - present_application_tables)
        raise LegacySchemaError(
            "Refusing to stamp a partial legacy schema; missing tables: " + ", ".join(missing)
        )

    revision, allowed_missing = _choose_revision(inspector)
    problems: list[str] = []
    for table_name in sorted(APPLICATION_TABLES):
        problems.extend(
            _validate_table(inspector, Base.metadata.tables[table_name], allowed_missing)
        )

    if problems:
        details = "\n - ".join(problems)
        raise LegacySchemaError(
            "Refusing to stamp an incompatible legacy schema:\n - " + details
        )

    migrations_dir = Path(__file__).resolve().parents[2] / "alembic"
    script = ScriptDirectory(str(migrations_dir))
    MigrationContext.configure(connection).stamp(script, revision)
    return revision


async def main() -> None:
    adopted_revision: str | None = None
    try:
        async with engine.begin() as connection:
            adopted_revision = await connection.run_sync(adopt_legacy_schema)
    finally:
        await engine.dispose()

    if adopted_revision:
        print(
            "✅ Compatible legacy schema detected; "
            f"Alembic history attached at {adopted_revision}."
        )
    else:
        print("ℹ️ Database is fresh or already tracked by Alembic.")


if __name__ == "__main__":
    asyncio.run(main())
