"""Handles database connections and operations."""

from pathlib import Path
from sqlite3 import Connection, connect
from threading import Lock
from typing import Any

from pydantic import BaseModel, Field, SkipValidation, field_validator, model_validator


class SQLiteHandlerConfig(BaseModel):
    """Configuration model for SQLiteHandler."""

    db_path: Path
    ddl_script: Path | None = None

    model_config = {
        "arbitrary_types_allowed": True,
    }

    @field_validator("db_path")
    @classmethod
    def check_db_path(cls, v: Path) -> Path:
        """Validate the db_path configuration attribute.

        Args:
        ----
            cls: The class of the configuration model.
            v (Path): The database path to be validated.

        Returns:
        -------
            Path: The validated database path.

        Raises:
        ------
            ValueError: If the database path is invalid.

        """
        if not v.parent.exists():
            err_msg = f"Invalid database path: {v}"
            raise ValueError(err_msg)
        return v

    @field_validator("ddl_script")
    @classmethod
    def check_ddl_script(cls, v: Path | None) -> Path | None:
        """Validate the ddl_script configuration attribute.

        Args:
        ----
            cls: The class of the configuration model.
            v (Path | None): The DDL script path to be validated.

        Returns:
        -------
            Path | None: The validated DDL script path.

        Raises:
        ------
            ValueError: If the DDL script path is invalid or the file does not exist.

        """
        if v and not v.is_file():
            err_msg = f"DDL script not found: {v}"
            raise ValueError(err_msg)
        return v


class SQLiteHandler(BaseModel):
    """SQLiteHandler class for managing SQLite database connections and operations."""

    config: SQLiteHandlerConfig
    write_conn: Connection = Field(init=False)
    read_conn: Connection = Field(init=False)
    lock: SkipValidation[Lock] = Field(default_factory=Lock, init=False)

    model_config = {
        "arbitrary_types_allowed": True,
    }

    @model_validator(mode="before")
    @classmethod
    def initialize_connections(cls, values: dict[str, Any]) -> dict[str, Any]:
        """Initialize database connections based on the provided configuration.

        Args:
        ----
            values (dict[str, Any]): A dictionary containing configuration values.

        Returns:
        -------
            dict[str, Any]: A dictionary with updated connection values.

        """
        config: SQLiteHandlerConfig = values["config"]

        write_conn = connect(
            config.db_path,
            timeout=5.0,
            isolation_level=None,  # Autocommit mode off
            check_same_thread=False,
        )
        cls._configure_connection(write_conn)

        read_conn = connect(
            config.db_path,
            timeout=5.0,
            isolation_level=None,
            check_same_thread=False,
        )
        cls._configure_connection(read_conn, readonly=True)

        values["write_conn"] = write_conn
        values["read_conn"] = read_conn

        # Optionally create the database schema if it doesn't exist
        if config.ddl_script and not config.db_path.exists():
            cls._create_schema(values, config.ddl_script)

        return values

    @staticmethod
    def _configure_connection(conn: Connection, readonly: bool = False) -> None:
        with conn:
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.execute("PRAGMA synchronous = NORMAL;")
            conn.execute("PRAGMA temp_store = MEMORY;")
            conn.execute("PRAGMA mmap_size = 30000000000;")
            conn.execute("PRAGMA busy_timeout = 5000;")

            if readonly:
                conn.execute("PRAGMA query_only = TRUE;")

    @staticmethod
    def _create_schema(values: dict[str, Any], ddl_script: Path) -> None:
        """Create the database schema using the provided DDL script."""
        write_conn: Connection = values["write_conn"]
        with write_conn as conn, ddl_script.open("r") as ddl_file:
            conn.executescript(ddl_file.read())
            conn.commit()

    def execute_write(
        self,
        query: str,
        params: dict[str, Any] | tuple[Any, ...] | None = None,
    ) -> int | None:
        """Execute a write operation."""
        with (  # pylint: disable=E1129
            self.lock,  # Ensure thread safety
            self.write_conn as conn,
        ):
            conn.execute("BEGIN IMMEDIATE;")
            cur = conn.execute(query, params or ())
            conn.commit()
            return cur.lastrowid

    def execute_read(
        self,
        query: str,
        params: dict[str, Any] | tuple[Any, ...] | None = None,
    ) -> list[Any]:
        """Execute a read operation."""
        with self.read_conn as conn:
            cur = conn.execute(query, params or ())
            return cur.fetchall()

    def optimize_database(self) -> None:
        """Optimize the database."""
        with self.write_conn as conn:
            conn.execute("PRAGMA optimize;")

    def close(self) -> None:
        """Close the database connections."""
        if self.write_conn:
            self.write_conn.close()
        if self.read_conn:
            self.read_conn.close()
