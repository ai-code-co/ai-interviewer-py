from __future__ import annotations

import argparse
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import sqlparse
from sqlalchemy import text

from ..db import get_engine


MIGRATION_FILE_RE = re.compile(r"^(\d+)_([a-z0-9_]+)\.sql$")
MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"

CREATE_MIGRATIONS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS schema_migrations (
  version BIGINT PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  checksum CHAR(64) NOT NULL,
  applied_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
)
"""


@dataclass(frozen=True)
class Migration:
    version: int
    name: str
    path: Path
    checksum: str


def _checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", name.strip().lower()).strip("_")
    return slug or "change"


def _discover_migrations() -> List[Migration]:
    if not MIGRATIONS_DIR.exists():
        return []

    items: List[Migration] = []
    seen: set[int] = set()
    for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
        match = MIGRATION_FILE_RE.match(path.name)
        if not match:
            raise RuntimeError(f"Invalid migration filename: {path.name}")
        version = int(match.group(1))
        if version in seen:
            raise RuntimeError(f"Duplicate migration version: {version}")
        seen.add(version)
        items.append(
            Migration(
                version=version,
                name=match.group(2),
                path=path,
                checksum=_checksum(path),
            )
        )
    items.sort(key=lambda m: m.version)
    return items


def _split_statements(sql: str) -> List[str]:
    statements = []
    for statement in sqlparse.split(sql):
        cleaned = statement.strip()
        if cleaned:
            statements.append(cleaned)
    return statements


def _ensure_migrations_table() -> None:
    engine = get_engine()
    with engine.begin() as conn:
        conn.exec_driver_sql(CREATE_MIGRATIONS_TABLE_SQL)


def _load_applied() -> Dict[int, dict]:
    _ensure_migrations_table()
    engine = get_engine()
    with engine.connect() as conn:
        rows = (
            conn.execute(
                text(
                    "SELECT version, name, checksum, applied_at "
                    "FROM schema_migrations ORDER BY version"
                )
            )
            .mappings()
            .all()
        )
    return {int(r["version"]): dict(r) for r in rows}


def _apply_migration(migration: Migration) -> None:
    sql = migration.path.read_text(encoding="utf-8")
    statements = _split_statements(sql)
    if not statements:
        raise RuntimeError(f"Migration has no SQL statements: {migration.path.name}")

    engine = get_engine()
    with engine.begin() as conn:
        for statement in statements:
            conn.exec_driver_sql(statement)
        conn.execute(
            text(
                "INSERT INTO schema_migrations (version, name, checksum) "
                "VALUES (:version, :name, :checksum)"
            ),
            {
                "version": migration.version,
                "name": migration.name,
                "checksum": migration.checksum,
            },
        )


def cmd_status() -> int:
    migrations = _discover_migrations()
    applied = _load_applied()

    if not migrations:
        print("No migration files found.")
        return 0

    print("Migration Status")
    print("----------------")
    for migration in migrations:
        row = applied.get(migration.version)
        if not row:
            print(f"pending  {migration.path.name}")
            continue
        if row["checksum"] != migration.checksum:
            print(f"changed  {migration.path.name} (checksum mismatch)")
            continue
        print(f"applied  {migration.path.name} at {row['applied_at']}")
    return 0


def cmd_up() -> int:
    migrations = _discover_migrations()
    applied = _load_applied()

    pending: List[Migration] = []
    for migration in migrations:
        row = applied.get(migration.version)
        if not row:
            pending.append(migration)
            continue
        if row["checksum"] != migration.checksum:
            raise RuntimeError(
                f"Applied migration changed on disk: {migration.path.name}. "
                "Create a new migration instead of editing old ones."
            )

    if not pending:
        print("No pending migrations.")
        return 0

    for migration in pending:
        print(f"Applying {migration.path.name} ...")
        _apply_migration(migration)
        print(f"Applied {migration.path.name}")
    return 0


def cmd_new(name: str) -> int:
    MIGRATIONS_DIR.mkdir(parents=True, exist_ok=True)
    existing = _discover_migrations()
    next_version = (existing[-1].version + 1) if existing else 1
    filename = f"{next_version:04d}_{_slugify(name)}.sql"
    path = MIGRATIONS_DIR / filename
    if path.exists():
        raise RuntimeError(f"Migration already exists: {path.name}")
    path.write_text(
        "-- Write forward-only SQL here.\n"
        "-- Do not edit old applied migrations; create a new file instead.\n\n",
        encoding="utf-8",
    )
    print(f"Created {path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="TiDB SQL migration runner")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("status", help="Show migration status")
    subparsers.add_parser("up", help="Apply pending migrations")

    new_parser = subparsers.add_parser("new", help="Create a new migration file")
    new_parser.add_argument("name", help="Migration name, e.g. add_candidate_index")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "status":
        return cmd_status()
    if args.command == "up":
        return cmd_up()
    if args.command == "new":
        return cmd_new(args.name)

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
