"""Database connection utilities for SQL Server."""

import os
import pyodbc
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def get_connection_string() -> str:
    """
    Build SQL Server connection string from environment variables.

    Returns:
        str: ODBC connection string

    Raises:
        ValueError: If required environment variables are missing
        Exception: If no suitable ODBC driver is found
    """
    host = os.getenv('DATABASE__HOST', 'localhost')
    port = os.getenv('DATABASE__PORT', '1433')
    database = os.getenv('DATABASE__DATABASE')
    user = os.getenv('DATABASE__USER')
    password = os.getenv('DATABASE__PASSWORD')

    if not all([database, user, password]):
        raise ValueError("Missing required environment variables. Check .env file.")

    # Try to find best available SQL Server ODBC driver
    drivers = pyodbc.drivers()
    preferred_drivers = [
        'ODBC Driver 18 for SQL Server',
        'ODBC Driver 17 for SQL Server',
        'ODBC Driver 13 for SQL Server',
        'SQL Server Native Client 11.0',
        'SQL Server'
    ]

    driver = None
    for pref_driver in preferred_drivers:
        if pref_driver in drivers:
            driver = pref_driver
            break

    if not driver:
        raise Exception(f"No suitable SQL Server ODBC driver found. Available: {drivers}")

    # SQL Server connection string
    conn_str = (
        f'DRIVER={{{driver}}};'
        f'SERVER={host},{port};'
        f'DATABASE={database};'
        f'UID={user};'
        f'PWD={password};'
        f'TrustServerCertificate=yes;'
    )
    return conn_str


def get_connection():
    """
    Get a connection to the database.

    Returns:
        pyodbc.Connection: Database connection object

    Raises:
        pyodbc.Error: If connection fails
    """
    try:
        conn_str = get_connection_string()
        conn = pyodbc.connect(conn_str)
        return conn
    except pyodbc.Error as e:
        print(f"Error connecting to database: {e}")
        print("\nAvailable ODBC drivers:")
        for driver in pyodbc.drivers():
            print(f"  - {driver}")
        raise
