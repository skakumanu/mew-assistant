#!/usr/bin/env python3
"""
Migration: three-persona scheduling (parent / kid / service provider).

Creates the new tables and adds the new columns on ``approval_requests``,
then seeds one RuleSet per parent from whatever the family already declared
through the older free-form ``ApprovalRule`` rows, so nobody re-enters their
rules.

Idempotent: safe to run repeatedly, and safe to run against a database that
already has some of the changes. Works on PostgreSQL and SQLite.

    DATABASE_URL=postgresql://... python scripts/migrate_three_persona_scheduling.py
    DATABASE_URL=... python scripts/migrate_three_persona_scheduling.py --dry-run
"""

from __future__ import annotations

import argparse
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import inspect, text  # noqa: E402

from app.database.connection import SessionLocal, engine  # noqa: E402
from app.database.models import (  # noqa: E402
    Base,
    ChangeLogEntry,
    ProtectedBlock,
    ProviderOrg,
    ProviderPerson,
    RuleSet,
    ScheduledSession,
    User,
    UserLocale,
    WeeklyCap,
)
from app.services.ruleset_service import RuleSetService  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("migrate")

NEW_TABLES = [
    ProviderOrg,
    ProviderPerson,
    ScheduledSession,
    RuleSet,
    ProtectedBlock,
    WeeklyCap,
    ChangeLogEntry,
    UserLocale,
]

# Column name -> type, per dialect. Everything is nullable, so the migration
# never has to invent values for rows that already exist.
NEW_APPROVAL_COLUMNS = {
    "requested_by": {"postgresql": "VARCHAR(20)", "sqlite": "VARCHAR(20)"},
    "provider_org_id": {"postgresql": "INTEGER", "sqlite": "INTEGER"},
    "change_kind": {"postgresql": "VARCHAR(20)", "sqlite": "VARCHAR(20)"},
    "scheduled_session_id": {"postgresql": "INTEGER", "sqlite": "INTEGER"},
    "new_start_utc": {"postgresql": "TIMESTAMP", "sqlite": "DATETIME"},
    "new_provider_person_id": {"postgresql": "INTEGER", "sqlite": "INTEGER"},
    "reason_codes": {"postgresql": "JSONB", "sqlite": "JSON"},
    "alternatives": {"postgresql": "JSONB", "sqlite": "JSON"},
    "auto_applied": {"postgresql": "BOOLEAN", "sqlite": "BOOLEAN"},
    "chosen_alternative_index": {"postgresql": "INTEGER", "sqlite": "INTEGER"},
}


def create_new_tables(dry_run: bool) -> None:
    inspector = inspect(engine)
    existing = set(inspector.get_table_names())
    missing = [model for model in NEW_TABLES if model.__tablename__ not in existing]

    if not missing:
        logger.info("All new tables already exist")
        return

    names = ", ".join(model.__tablename__ for model in missing)
    if dry_run:
        logger.info("[dry run] would create: %s", names)
        return

    Base.metadata.create_all(bind=engine, tables=[model.__table__ for model in missing])
    logger.info("Created: %s", names)


def add_approval_columns(dry_run: bool) -> None:
    inspector = inspect(engine)
    if "approval_requests" not in inspector.get_table_names():
        logger.info("approval_requests does not exist yet; create_all will handle it")
        return

    dialect = engine.dialect.name
    existing = {column["name"] for column in inspector.get_columns("approval_requests")}

    for name, types in NEW_APPROVAL_COLUMNS.items():
        if name in existing:
            continue
        column_type = types.get(dialect, types["sqlite"])
        statement = f"ALTER TABLE approval_requests ADD COLUMN {name} {column_type}"
        if dry_run:
            logger.info("[dry run] %s", statement)
            continue
        with engine.begin() as connection:
            connection.execute(text(statement))
        logger.info("Added approval_requests.%s", name)


# Columns added to tables this migration created in an earlier run.
LATE_COLUMNS = {
    "rule_sets": {
        "caregiver_term": {"postgresql": "VARCHAR(20)", "sqlite": "VARCHAR(20)"},
    },
}


def add_late_columns(dry_run: bool) -> None:
    """Add columns introduced after a table was first created."""
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    dialect = engine.dialect.name

    for table, columns in LATE_COLUMNS.items():
        if table not in tables:
            continue  # create_all just made it, with every column
        existing = {column["name"] for column in inspector.get_columns(table)}
        for name, types in columns.items():
            if name in existing:
                continue
            column_type = types.get(dialect, types["sqlite"])
            statement = f"ALTER TABLE {table} ADD COLUMN {name} {column_type}"
            if dry_run:
                logger.info("[dry run] %s", statement)
                continue
            with engine.begin() as connection:
                connection.execute(text(statement))
            logger.info("Added %s.%s", table, name)


def seed_rulesets(dry_run: bool) -> None:
    """One RuleSet per parent, seeded from any older ApprovalRule rows."""
    session = SessionLocal()
    try:
        parents = (
            session.query(User)
            .filter(User.is_kid_account.is_(False), User.is_active.is_(True))
            .all()
        )
        service = RuleSetService(session)
        created = 0

        for parent in parents:
            children = session.query(User).filter(User.parent_id == parent.id).all()
            if not children:
                continue
            for child in children:
                if service.get(parent.id, child.id) is not None:
                    continue
                if dry_run:
                    logger.info(
                        "[dry run] would seed rules for parent %s / child %s",
                        parent.id,
                        child.id,
                    )
                    continue
                service.get_or_create(parent.id, child.id)
                created += 1

        if created:
            logger.info("Seeded %s rule set(s) from existing approval rules", created)
        else:
            logger.info("No rule sets needed seeding")
    finally:
        session.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Print what would change and stop")
    parser.add_argument(
        "--skip-seed", action="store_true", help="Schema only, no rule-set backfill"
    )
    args = parser.parse_args()

    if not os.getenv("DATABASE_URL"):
        logger.warning("DATABASE_URL is not set; using the default from app config")

    try:
        create_new_tables(args.dry_run)
        add_approval_columns(args.dry_run)
        add_late_columns(args.dry_run)
        if not args.skip_seed:
            seed_rulesets(args.dry_run)
    except Exception as error:
        logger.error("Migration failed: %s", error)
        return 1

    logger.info("Done%s", " (dry run)" if args.dry_run else "")
    return 0


if __name__ == "__main__":
    sys.exit(main())
