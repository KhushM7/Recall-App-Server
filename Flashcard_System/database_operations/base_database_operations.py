import sqlite3
import logging
from abc import ABC, abstractmethod
from typing import List, Any, Tuple, Optional

# Configure logging
logging.basicConfig(
    filename="../physics_server_log.log",
    filemode="a",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


class BaseDatabaseOperations(ABC):
    def __init__(self, conn: sqlite3.Connection):
        if conn is None:
            raise ValueError("Database connection cannot be None")
        self.conn = conn

    @abstractmethod
    def fetch(self, query: str, params: Tuple = ()) -> List[Any]:
        """Execute a SELECT query and return the results."""
        try:
            logging.info(f"Executing query: {query} with params: {params}")
            cursor = self.conn.execute(query, params)
            result = [dict(row) for row in cursor.fetchall()]
            logging.info(f"Fetched {len(result)} rows")
            return result
        except sqlite3.Error as e:
            logging.error(f"Error fetching data: {e}")
            raise RuntimeError(f"Database error: {e}")

    @abstractmethod
    def fetch_one(self, query: str, params: Tuple = ()) -> Optional[Any]:
        """Execute a SELECT query and return a single row."""
        try:
            logging.info(f"Executing query (fetch one): {query} with params: {params}")
            cursor = self.conn.execute(query, params)
            result = cursor.fetchone()
            if result:
                logging.info(f"Fetched row: {dict(result)}")
                return dict(result)
            logging.info("No rows found")
            return None
        except sqlite3.Error as e:
            logging.error(f"Error fetching data: {e}")
            raise RuntimeError(f"Database error: {e}")

    @abstractmethod
    def insert(self, query: str, params: Tuple = ()) -> None:
        """Execute an INSERT query."""
        try:
            if not params:
                raise ValueError("Insert operation requires parameters.")
            logging.info(f"Inserting with query: {query} and params: {params}")
            with self.conn:
                self.conn.execute(query, params)
            logging.info("Insert operation successful")
        except sqlite3.Error as e:
            logging.error(f"Error during insert: {e}")
            raise RuntimeError(f"Database error: {e}")

    @abstractmethod
    def update(self, query: str, params: Tuple = ()) -> None:
        """Execute an UPDATE query."""
        try:
            if not params:
                raise ValueError("Update operation requires parameters.")
            logging.info(f"Updating with query: {query} and params: {params}")
            with self.conn:
                self.conn.execute(query, params)
            logging.info("Update operation successful")
        except sqlite3.Error as e:
            logging.error(f"Error during update: {e}")
            raise RuntimeError(f"Database error: {e}")

    @abstractmethod
    def delete(self, query: str, params: Tuple = ()) -> None:
        """Execute a DELETE query."""
        try:
            if not params:
                raise ValueError("Delete operation requires parameters.")
            logging.info(f"Deleting with query: {query} and params: {params}")
            with self.conn:
                self.conn.execute(query, params)
            logging.info("Delete operation successful")
        except sqlite3.Error as e:
            logging.error(f"Error during delete: {e}")
            raise RuntimeError(f"Database error: {e}")
