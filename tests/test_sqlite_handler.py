"""Test SQLiteHandler."""

from pathlib import Path
from sqlite3 import Connection
from tempfile import TemporaryDirectory  # pyright: ignore [reportUnknownVariableType]
from typing import Any, Callable
import pytest
from pytest_mock import MockFixture
from rssphere.database.sqlite_handler import SQLiteHandler, SQLiteHandlerConfig


@pytest.fixture
def sqlite_handler_setup(mocker: MockFixture):
    """Fixture to set up common SQLiteHandler dependencies."""

    # Mock the connect function to return a mock connection
    mock_connect = mocker.patch(
        "rssphere.database.sqlite_handler.connect", autospec=True
    )
    mock_conn = mocker.Mock(spec=Connection)

    mock_enter: Callable[[Any], Any] = lambda s: s
    mock_conn.__enter__ = mock_enter
    mock_exit: Callable[[Any, Any, Any, Any], None] = (
        lambda s, exc_type, exc_val, exc_tb: None
    )
    mock_conn.__exit__ = mock_exit
    mock_connect.return_value = mock_conn

    # Mock the Path.exists method to return True
    mocker.patch("pathlib.Path.exists", return_value=True)

    # Create a valid configuration
    config = SQLiteHandlerConfig(db_path=Path("/valid/path/to/db.sqlite"))

    # Return a tuple or a dictionary with all necessary items
    return {"mock_connect": mock_connect, "mock_conn": mock_conn, "config": config}


def test_valid_existing_db_path_with_temporary_directory():
    """Valid existing db_path is returned correctly after creating a temporary directory."""
    with (
        TemporaryDirectory() as temp_dir  # pyright: ignore [reportUnknownVariableType]
    ):
        valid_path = (
            Path(temp_dir)  # pyright: ignore [reportUnknownArgumentType]
            / "database.db"
        )
        config = SQLiteHandlerConfig(db_path=valid_path)
        assert config.db_path == valid_path


def test_invalid_db_path():
    """Invalid db_path raises ValueError."""
    invalid_path = Path("/invalid/path/to/database.db")
    with pytest.raises(ValueError, match="Invalid database path"):
        SQLiteHandlerConfig(db_path=invalid_path)


def test_initialize_sqlite_handler_valid_config(
    sqlite_handler_setup: dict[str, Any]  # pylint: disable=W0621
):
    """Initialize SQLiteHandler with valid configuration and mock Path.exists."""
    handler = SQLiteHandler(config=sqlite_handler_setup["config"])

    # Assertions
    assert handler.write_conn == sqlite_handler_setup["mock_conn"]
    assert handler.read_conn == sqlite_handler_setup["mock_conn"]
    sqlite_handler_setup["mock_connect"].assert_called_with(  # type: ignore
        Path("/valid/path/to/db.sqlite"),
        timeout=5.0,
        isolation_level=None,
        check_same_thread=False,
    )


def test_execute_write_success(
    sqlite_handler_setup: dict[str, Any], mocker: MockFixture  # pylint: disable=W0621
):
    """Execute write operation successfully with a valid database path."""
    handler = SQLiteHandler(config=sqlite_handler_setup["config"])

    # Mock the execute method of the connection
    mock_execute = mocker.patch.object(sqlite_handler_setup["mock_conn"], "execute")

    # Call the execute_write method
    result = handler.execute_write("INSERT INTO table (column) VALUES (?)", (123,))

    # Assertions
    assert result is not None
    sqlite_handler_setup["mock_connect"].assert_called_with(  # type: ignore
        Path("/valid/path/to/db.sqlite"),
        timeout=5.0,
        isolation_level=None,
        check_same_thread=False,
    )
    mock_execute.assert_called_with("INSERT INTO table (column) VALUES (?)", (123,))


def test_execute_read_success(
    sqlite_handler_setup: dict[str, Any], mocker: MockFixture  # pylint: disable=W0621
):
    """Execute read operation successfully with a valid database path."""
    handler = SQLiteHandler(config=sqlite_handler_setup["config"])

    # Mock the execute method of the read connection
    mock_execute = mocker.patch.object(sqlite_handler_setup["mock_conn"], "execute")
    mock_execute.return_value.fetchall.return_value = ["result1", "result2"]

    # Call the execute_read method
    results = handler.execute_read("SELECT * FROM table")

    # Assertions
    assert results == ["result1", "result2"]
    mock_execute.assert_called_with("SELECT * FROM table", ())


def test_optimize_database(
    sqlite_handler_setup: dict[str, Any], mocker: MockFixture  # pylint: disable=W0621
):
    """Optimize database successfully with a valid database path."""
    handler = SQLiteHandler(config=sqlite_handler_setup["config"])
    mock_execute = mocker.patch.object(sqlite_handler_setup["mock_conn"], "execute")
    handler.optimize_database()
    mock_execute.assert_called_with("PRAGMA optimize;")


def test_close_database_connections_properly(
    sqlite_handler_setup: dict[str, Any], mocker: MockFixture  # pylint: disable=W0621
):
    """Close database connections properly with a valid configuration and fixed db_path"""
    handler = SQLiteHandler(config=sqlite_handler_setup["config"])
    handler.write_conn = mocker.MagicMock()
    handler.read_conn = mocker.MagicMock()

    handler.close()

    handler.write_conn.close.assert_called_once()  # type: ignore
    handler.read_conn.close.assert_called_once()  # type: ignore
