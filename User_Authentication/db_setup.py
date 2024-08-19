import sqlite3
from sqlite3 import Error
from typing import Optional


def create_connection(db_file_name: str) -> Optional[sqlite3.Connection]:
    try:
        conn = sqlite3.connect(db_file_name)
        return conn
    except Error as e:
        print(e)
        return None


def create_table(conn: sqlite3.Connection, create_table_sql: str) -> None:
    try:
        cursor = conn.cursor()
        cursor.execute(create_table_sql)
        conn.commit()
    except Error as e:
        print(e)


def main() -> None:
    database_name = "physics_revision_app.db"

    sql_create_users_table = """ CREATE TABLE IF NOT EXISTS Users (
                                        user_id integer PRIMARY KEY Autoincrement,
                                        email text NOT NULL,
                                        username text NOT NULL,
                                        password text NOT NULL
                                    ); """

    conn = create_connection(database_name)

    if conn is not None:
        create_table(conn, sql_create_users_table)
        conn.close()
    else:
        print("Error! cannot create the database connection.")


if __name__ == "__main__":
    main()
