import os

import mysql.connector
from dotenv import load_dotenv

load_dotenv()


def create_connection():
    """Open a connection to the employee MySQL database."""
    required_settings = ["DB_HOST", "DB_USER", "DB_NAME"]
    missing_settings = [
        setting for setting in required_settings if not os.getenv(setting)
    ]

    if missing_settings:
        missing_names = ", ".join(missing_settings)
        raise ValueError(
            f"Missing database settings: {missing_names}. Add them to your .env file."
        )

    try:
        port = int(os.getenv("DB_PORT", "3306"))
    except ValueError as error:
        raise ValueError("DB_PORT must be a whole number, such as 3306.") from error

    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            port=port,
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME"),
        )
    except mysql.connector.Error as error:
        raise RuntimeError(
            "Could not connect to MySQL. Check that the server is running "
            "and that your .env settings are correct. "
            f"MySQL reported: {error}"
        ) from error

    return connection
