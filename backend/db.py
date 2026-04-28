import os
import json
import psycopg
from psycopg_pool import ConnectionPool
from psycopg.rows import dict_row
from contextlib import contextmanager

base_dir = os.path.dirname(os.path.abspath(__file__))
db_config_filepath = os.path.join(base_dir, "database_config.json")

with open(db_config_filepath) as f:
    db_config = json.load(f)

# Initialize the pool globally
# min_size=1 keeps one connection warm; max_size limits total connections
pool = ConnectionPool(
    conninfo=" ".join([f"{k}={v}" for k, v in db_config.items()]),
    min_size=1,
    max_size=10,
    kwargs={"row_factory": dict_row}, # Now every query returns a dict by default
    open=True
)

def execute_query(query, params=None, fetch=False) -> list | dict | None: 
    # Use the pool to get a connection
    with pool.connection() as conn:
        # In psycopg 3, the connection context manager handles commits/rollbacks
        with conn.cursor() as cur:
            cur.execute(query, params)
            
            if fetch:
                # fetchall() is fine, but fetchone() might be safer for single rows
                return cur.fetchall()
            return None


@contextmanager
def transaction_connection(isolation_level: str = "SERIALIZABLE"):
    with pool.connection() as conn:
        conn.execute("BEGIN")
        conn.execute(f"SET TRANSACTION ISOLATION LEVEL {isolation_level}")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise

# Ensure the pool closes when the app shuts down
def close_pool():
    pool.close()
