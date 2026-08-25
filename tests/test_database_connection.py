"""
init_db()'s advisory-lock queries against PostgreSQL.

SQLAlchemy 2.0's Connection.execute() rejects a bare Python string
(ObjectNotExecutableError) - it must be wrapped in text(). That exact
mistake here silently killed create_all() in production: the surrounding
except Exception logged a warning and moved on, so every boot left the
schema completely empty. The tests use SQLite everywhere else, which never
takes this code path at all, so nothing caught it before it shipped.
"""

import asyncio
from unittest.mock import MagicMock, patch

from sqlalchemy.sql.elements import TextClause

from app.database import connection as connection_module


class _FakeResult:
    def __init__(self, value):
        self._value = value

    def scalar(self):
        return self._value


class _FakeConnection:
    def __init__(self):
        self.executed = []

    def execute(self, clause):
        self.executed.append(clause)
        # First call is the lock attempt (truthy = acquired), second is
        # the unlock on the way out.
        return _FakeResult(True)

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False


def test_advisory_lock_queries_are_wrapped_in_text(monkeypatch):
    fake_connection = _FakeConnection()
    fake_engine = MagicMock()
    fake_engine.connect.return_value = fake_connection

    monkeypatch.setattr(connection_module, "DATABASE_URL", "postgresql://x/y")
    monkeypatch.setattr(connection_module, "engine", fake_engine)

    with patch("app.database.models.Base") as mock_base:
        mock_base.metadata.create_all = MagicMock()
        asyncio.run(connection_module.init_db())
        assert mock_base.metadata.create_all.called

    assert fake_connection.executed, "the advisory-lock query never ran"
    assert all(isinstance(clause, TextClause) for clause in fake_connection.executed), (
        "a bare string was passed to Connection.execute() - SQLAlchemy 2.0 "
        "raises ObjectNotExecutableError for that at runtime, which the "
        "outer except Exception in init_db() swallows as a warning"
    )
