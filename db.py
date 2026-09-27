import mysql.connector
from mysql.connector import pooling, Error
from config import Config
from contextlib import contextmanager

# Initialize MySQL Connection Pool
try:
    db_pool = pooling.MySQLConnectionPool(
        pool_name="lms_pool",
        pool_size=5,
        pool_reset_session=True,
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        autocommit=False
    )
except Error as e:
    db_pool = None
    print(f"Warning: Failed to create connection pool: {e}")

def get_db_connection():
    """Retrieve a connection from pool or fallback to direct connection."""
    global db_pool
    if db_pool:
        try:
            return db_pool.get_connection()
        except Error:
            pass
    return mysql.connector.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        autocommit=False
    )

def query_db(query, args=(), one=False):
    """Execute a SELECT query and return dictionary results."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, args)
        rv = cursor.fetchall()
        cursor.close()
        return (rv[0] if rv else None) if one else rv
    finally:
        conn.close()

def execute_db(query, args=(), commit=True):
    """Execute an INSERT, UPDATE, or DELETE query."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, args)
        last_id = cursor.lastrowid
        row_count = cursor.rowcount
        cursor.close()
        if commit:
            conn.commit()
        return {'lastrowid': last_id, 'rowcount': row_count}
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

@contextmanager
def get_db_transaction():
    """
    Context manager for atomic multi-statement database transactions (TCL).
    Automatically commits on success or rolls back on exception.
    """
    conn = get_db_connection()
    conn.start_transaction()
    cursor = conn.cursor(dictionary=True)
    try:
        yield cursor
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()
