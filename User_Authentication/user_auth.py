import sqlite3
import logging
from typing import Tuple, Optional
import bcrypt

# Configure the centralized logger
logging.basicConfig(
    filename="application.log",
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class UserAuthentication:
    def __init__(self, db_path: str):
        self.db_path = db_path
        logger.info("UserAuthentication initialized with database path: %s", db_path)

    def insert_user_into_db(self, email: str, username: str, password: str):
        """Inserts a new user into the database and hashes the password."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        try:
            cursor.execute(
                "INSERT INTO Users (email, username, password) VALUES (?, ?, ?);",
                (email, username, hashed_password),
            )
            cursor.execute(
                "INSERT INTO UserSettings (user_id) VALUES ((SELECT user_id FROM Users WHERE email = ?));",
                (email,),
            )
            conn.commit()
            logger.info("User %s successfully inserted into the database.", username)
        except sqlite3.IntegrityError:
            logger.error(
                "Failed to insert user %s: Username or email already exists.", username
            )
            raise ValueError("Username or email already exists!")
        finally:
            conn.close()

    def confirm_user_details(
        self, email_username: str, password: str
    ) -> Tuple[bool, Optional[str]]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        if "@" in email_username:
            query = "SELECT password FROM Users WHERE email = ?;"
        else:
            query = "SELECT password FROM Users WHERE username = ?;"
        cursor.execute(query, (email_username,))
        user_password = cursor.fetchone()
        conn.close()
        if user_password:
            if bcrypt.checkpw(password.encode("utf-8"), user_password[0]):
                logger.info("User %s successfully authenticated.", email_username)
                return True, None
            else:
                logger.warning(
                    "User %s failed authentication: Incorrect password.", email_username
                )
                return False, "Incorrect password!"
        else:
            logger.warning("Authentication failed: %s does not exist.", email_username)
            return False, "Username or email does not exist!"

    def update_password(self, email: str, new_password: str) -> bool:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            hashed_password = bcrypt.hashpw(
                new_password.encode("utf-8"), bcrypt.gensalt()
            )
            cursor.execute(
                "UPDATE Users SET password = ? WHERE email = ?",
                (hashed_password, email),
            )
            conn.commit()
            logger.info("Password updated successfully for email: %s", email)
            return True
        except Exception as e:
            logger.error("Failed to update password for email %s: %s", email, e)
            return False
        finally:
            conn.close()

    def is_email_taken(self, email: str) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT email FROM Users WHERE email = ?", (email,))
            fetch = cursor.fetchone()
            is_taken = fetch is not None
            logger.info("Email %s taken status: %s", email, is_taken)
            return is_taken
        except sqlite3.Error as e:
            logger.error("Database error while checking email %s: %s", email, e)
            return False
        finally:
            conn.close()

    def is_username_taken(self, username: str) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT username FROM Users WHERE username = ?", (username,))
            fetch = cursor.fetchone()
            is_taken = fetch is not None
            logger.info("Username %s taken status: %s", username, is_taken)
            return is_taken
        except sqlite3.Error as e:
            logger.error("Database error while checking username %s: %s", username, e)
            return False
        finally:
            conn.close()

    def get_user_id(self, email_or_username: str) -> Optional[int]:
        """
        Retrieve the user ID based on the email or username.

        :param email_or_username: The email or username of the user.
        :return: User ID if found, otherwise None.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            if "@" in email_or_username:  # Check if the input is an email
                cursor.execute(
                    "SELECT user_id FROM Users WHERE email = ?", (email_or_username,)
                )
            else:
                cursor.execute(
                    "SELECT user_id FROM Users WHERE username = ?", (email_or_username,)
                )
            result = cursor.fetchone()
            user_id = result[0] if result else None
            logger.info("Retrieved user ID for %s: %s", email_or_username, user_id)
            return user_id
        finally:
            conn.close()

    def get_username(self, user_id: int) -> Optional[str]:
        """
        Retrieve the username based on the user ID.

        :param user_id: The ID of the user.
        :return: The username if found, otherwise None.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT username FROM Users WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            username = result[0] if result else None
            logger.info("Retrieved username for user ID %d: %s", user_id, username)
            return username
        finally:
            conn.close()

    def update_email(self, user_id: int, new_email: str) -> bool:
        """
        Update the email for a user by sending the new email to the server.

        :param user_id: The ID of the user.
        :param new_email: The new email for the user.
        :return: True if the email was updated successfully, False otherwise.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE Users SET email = ? WHERE user_id = ?", (new_email, user_id)
            )
            conn.commit()
            logger.info("Email updated successfully for user ID: %d", user_id)
            return True
        except sqlite3.Error as e:
            logger.error("Failed to update email for user ID %d: %s", user_id, e)
            return False
        finally:
            conn.close()

    def update_username(self, user_id: int, new_username: str) -> bool:
        """
        Update the username for a user by sending the new username to the server.

        :param user_id: The ID of the user.
        :param new_username: The new username for the user.
        :return: True if the username was updated successfully, False otherwise.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE Users SET username = ? WHERE user_id = ?",
                (new_username, user_id),
            )
            conn.commit()
            logger.info("Username updated successfully for user ID: %d", user_id)
            return True
        except sqlite3.Error as e:
            logger.error("Failed to update username for user ID %d: %s", user_id, e)
            return False
        finally:
            conn.close()

    def get_email(self, user_id: int) -> Optional[str]:
        """
        Retrieve the email based on user ID.

        :param user_id: The ID of the user.
        :return: Email if found, otherwise None.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT email FROM Users WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            email = result[0] if result else None
            logger.info("Retrieved email for user ID %d: %s", user_id, email)
            return email
        finally:
            conn.close()
