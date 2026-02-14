from __future__ import annotations

import json
from contextlib import contextmanager
from datetime import datetime
from functools import lru_cache
from typing import Any, Dict, Generator, Iterable, Optional

import certifi
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.engine import Connection, Result

from .config import get_settings


@lru_cache()
def get_engine() -> Engine:
    settings = get_settings()
    connect_args: Dict[str, Any] = {}
    if settings.db_ssl_enabled:
        ca_path = settings.db_ssl_ca or certifi.where()
        connect_args.update(
            {
                "ssl": {"ca": ca_path},
                "ssl_verify_cert": settings.db_ssl_verify_cert,
                "ssl_verify_identity": settings.db_ssl_verify_identity,
            }
        )
    return create_engine(
        settings.sqlalchemy_database_url,
        pool_pre_ping=True,
        connect_args=connect_args,
        future=True,
    )


@contextmanager
def db_connection(transactional: bool = False) -> Generator[Connection, None, None]:
    engine = get_engine()
    if transactional:
        with engine.begin() as conn:
            yield conn
    else:
        with engine.connect() as conn:
            yield conn


def execute(sql: str, params: Optional[Dict[str, Any]] = None, conn: Optional[Connection] = None) -> Result[Any]:
    payload = params or {}
    if conn is not None:
        return conn.execute(text(sql), payload)
    with db_connection(transactional=True) as owned_conn:
        return owned_conn.execute(text(sql), payload)


def fetch_all(sql: str, params: Optional[Dict[str, Any]] = None, conn: Optional[Connection] = None) -> list[Dict[str, Any]]:
    payload = params or {}
    if conn is not None:
        result = conn.execute(text(sql), payload)
        return [_row_to_dict(r._mapping) for r in result]
    with db_connection() as owned_conn:
        result = owned_conn.execute(text(sql), payload)
        return [_row_to_dict(r._mapping) for r in result]


def fetch_one(sql: str, params: Optional[Dict[str, Any]] = None, conn: Optional[Connection] = None) -> Dict[str, Any] | None:
    payload = params or {}
    if conn is not None:
        result = conn.execute(text(sql), payload).first()
        return _row_to_dict(result._mapping) if result else None
    with db_connection() as owned_conn:
        result = owned_conn.execute(text(sql), payload).first()
        return _row_to_dict(result._mapping) if result else None


def to_json_db(value: Any) -> str:
    return json.dumps(value if value is not None else [])


def from_json_db(value: Any, default: Any) -> Any:
    if value is None:
        return default
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, (bytes, bytearray)):
        try:
            value = value.decode("utf-8")
        except Exception:
            return default
    if isinstance(value, str):
        try:
            return json.loads(value)
        except Exception:
            return default
    return default


def _row_to_dict(mapping: Iterable[tuple[str, Any]] | Any) -> Dict[str, Any]:
    row: Dict[str, Any] = {}
    for key, value in dict(mapping).items():
        if isinstance(value, datetime):
            row[key] = value.isoformat()
        else:
            row[key] = value
    return row
