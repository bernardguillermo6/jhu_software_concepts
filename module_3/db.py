#!/usr/bin/env python3
import psycopg

def get_db_connection():
    """initialize a postgres db connection"""
    
    return psycopg.connect(dbname="thegradcafe", user="postgres", host="localhost", port=5432)
