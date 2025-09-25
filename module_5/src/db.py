#!/usr/bin/env python3
"""
Database connection helper for the Grad Cafe application.

Provides a single function `get_db_connection()` which connects to
PostgreSQL using the DATABASE_URL environment variable if available,
otherwise falling back to a default local connection.
"""

import os

import psycopg


def get_db_connection():
    """
    Initialize and return a PostgreSQL database connection.

    Uses the `DATABASE_URL` environment variable if defined,
    otherwise falls back to:
        dbname=thegradcafe user=postgres host=localhost port=5432

    Returns
    -------
    psycopg.Connection
        A live connection to PostgreSQL.
    """
    connection_string = os.getenv(
        "DATABASE_URL", "dbname=thegradcafe user=postgres host=localhost port=5432"
    )
    return psycopg.connect(connection_string)
