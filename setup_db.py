import sqlite3


def initialize_db():
    """Create the database and the table to store OTPs."""
    conn = sqlite3.connect("otp_db.sqlite3")
    c = conn.cursor()

    c.execute(
        """
    CREATE TABLE IF NOT EXISTS otp (
        email TEXT PRIMARY KEY,
        otp TEXT NOT NULL,
        expiry REAL NOT NULL
    )
    """
    )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    initialize_db()
