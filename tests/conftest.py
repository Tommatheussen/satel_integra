"""Shared pytest fixtures for the test suite."""

from unittest.mock import AsyncMock
import pytest

from satel_integra.satel_integra import AsyncSatel


@pytest.fixture
def mock_queue():
    """A simple AsyncMock queue used by many tests."""
    queue = AsyncMock()
    return queue


@pytest.fixture
def mock_connection():
    """A generic async connection mock for tests that need a connected backend.

    Note: test modules that need a more specific `mock_connection` can still
    define their own fixture which will shadow this one.
    """
    conn = AsyncMock()
    conn.connected = True
    conn.closed = False
    return conn


@pytest.fixture
def satel(monkeypatch, mock_connection, mock_queue):
    """Create an `AsyncSatel` instance with the underlying connection/queue
    monkeypatched to the provided mocks.
    """
    # Monkeypatch the concrete classes used when AsyncSatel constructs
    monkeypatch.setattr(
        "satel_integra.satel_integra.SatelConnection", lambda *a, **kw: mock_connection
    )
    monkeypatch.setattr(
        "satel_integra.satel_integra.SatelMessageQueue", lambda send: mock_queue
    )

    stl = AsyncSatel(
        "127.0.0.1",
        7094,
        monitored_zones=[1, 2],
        monitored_outputs=[3, 4],
        partitions=[1],
    )

    # Ensure the instance uses our mocks
    stl._connection = mock_connection
    stl._queue = mock_queue
    return stl
