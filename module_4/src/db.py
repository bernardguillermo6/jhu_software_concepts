#!/usr/bin/env python3
import psycopg


def get_db_connection():
    """Initialize and return a PostgreSQL database connection.

    Input:
        None.

    Output:
        psycopg.connection: A live connection to the thegradcafe database
        using user 'postgres' on localhost:5432.
    """
    return psycopg.connect(dbname="thegradcafe", user="postgres", host="localhost", port=5432)
