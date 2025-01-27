import sqlite3
import logging
from abc import ABC, abstractmethod
from typing import List, Any, Tuple, Optional

# Configure logging
logging.basicConfig(
    filename="application.log",
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class BaseDatabaseOperations(ABC):
    def __init__(self, conn: sqlite3.Connection):
        if conn is None:
            logger.error("Database connection cannot be None")
            raise ValueError("Database connection cannot be None")
        self.conn = conn

    @abstractmethod
    def fetch(self, query: str, params: Tuple = ()) -> List[Any]:
        """Execute a SELECT query and return the results."""
        try:
            logger.info("Executing query: %s with params: %s", query, params)
            cursor = self.conn.execute(query, params)
            result = [dict(row) for row in cursor.fetchall()]
            logger.info("Fetched %d rows", len(result))
            return result
        except sqlite3.Error as e:
            logger.error("Error fetching data: %s", e)
            raise RuntimeError(f"Database error: {e}")

    @abstractmethod
    def fetch_one(self, query: str, params: Tuple = ()) -> Optional[Any]:
        """Execute a SELECT query and return a single row."""
        try:
            logger.info(
                "Executing query (fetch one): %s with params: %s", query, params
            )
            cursor = self.conn.execute(query, params)
            result = cursor.fetchone()
            if result:
                logger.info("Fetched row: %s", dict(result))
                return dict(result)
            logger.info("No rows found")
            return None
        except sqlite3.Error as e:
            logger.error("Error fetching data: %s", e)
            raise RuntimeError(f"Database error: {e}")

    @abstractmethod
    def insert(self, query: str, params: Tuple = ()) -> None:
        """Execute an INSERT query."""
        try:
            if not params:
                logger.error("Insert operation requires parameters.")
                raise ValueError("Insert operation requires parameters.")
            logger.info("Inserting with query: %s and params: %s", query, params)
            with self.conn:
                self.conn.execute(query, params)
            logger.info("Insert operation successful")
        except sqlite3.Error as e:
            logger.error("Error during insert: %s", e)
            raise RuntimeError(f"Database error: {e}")

    @abstractmethod
    def update(self, query: str, params: Tuple = ()) -> None:
        """Execute an UPDATE query."""
        try:
            if not params:
                logger.error("Update operation requires parameters.")
                raise ValueError("Update operation requires parameters.")
            logger.info("Updating with query: %s and params: %s", query, params)
            with self.conn:
                self.conn.execute(query, params)
            logger.info("Update operation successful")
        except sqlite3.Error as e:
            logger.error("Error during update: %s", e)
            raise RuntimeError(f"Database error: {e}")

    @abstractmethod
    def delete(self, query: str, params: Tuple = ()) -> None:
        """Execute a DELETE query."""
        try:
            if not params:
                logger.error("Delete operation requires parameters.")
                raise ValueError("Delete operation requires parameters.")
            logger.info("Deleting with query: %s and params: %s", query, params)
            with self.conn:
                self.conn.execute(query, params)
            logger.info("Delete operation successful")
        except sqlite3.Error as e:
            logger.error("Error during delete: %s", e)
            raise RuntimeError(f"Database error: {e}")
