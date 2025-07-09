# db_pool.py

import os
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from contextlib import contextmanager

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

db_pool = None


def init_db_pool():
    """Initializes the database connection pool."""
    global db_pool
    if db_pool:
        return
    try:
        db_pool = psycopg2.pool.SimpleConnectionPool(
            minconn=1, maxconn=20, dsn=DATABASE_URL, cursor_factory=RealDictCursor
        )
        print("Database connection pool created successfully (PostgreSQL).")
    except psycopg2.OperationalError as e:
        print(f"FATAL: Could not create connection pool for PostgreSQL: {e}")
        raise


@contextmanager
def get_db_cursor(commit=False):
    """Context manager to get a cursor from the connection pool."""
    if not db_pool:
        raise RuntimeError("Database pool is not initialized.")
    conn = db_pool.getconn()
    try:
        with conn.cursor() as cur:
            yield cur
            if commit:
                conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        db_pool.putconn(conn)