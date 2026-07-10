from __future__ import annotations

from sqlalchemy import inspect, select
from sqlalchemy.orm import Session

from .database import Base, Database
from .models import SchemaMigration


MIGRATIONS = [
    (
        "0001",
        "Initial universal entity registry, relationships, aliases, evidence foundations, validation events, and import jobs.",
    ),
]


def run_migrations(database: Database) -> list[str]:
    # v2.0.0 uses a cross-database SQLAlchemy migration foundation.
    # Later releases append explicit migration functions while preserving this ledger.
    Base.metadata.create_all(database.engine)
    applied: list[str] = []

    with database.session_factory() as session:
        for version, description in MIGRATIONS:
            existing = session.get(SchemaMigration, version)
            if existing is None:
                session.add(
                    SchemaMigration(
                        version=version,
                        description=description,
                    )
                )
                session.commit()
                applied.append(version)

    return applied


def migration_status(database: Database) -> dict:
    Base.metadata.create_all(database.engine)
    with database.session_factory() as session:
        applied = {
            row.version
            for row in session.scalars(select(SchemaMigration)).all()
        }
    expected = {version for version, _ in MIGRATIONS}
    return {
        "expected": sorted(expected),
        "applied": sorted(applied),
        "pending": sorted(expected - applied),
    }
